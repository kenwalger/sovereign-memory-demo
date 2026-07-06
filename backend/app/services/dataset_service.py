"""Fail-fast dataset ingestion for the institutional memory demo."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.content_filters import strip_author_footers
from app.models import (
    AccessionRecordSchema,
    Document,
    PhotographRecordSchema,
    Record,
)
from app.services.exceptions import (
    DatasetEncodingError,
    DatasetFileNotFoundError,
    DatasetSchemaError,
    DatasetValidationError,
)

REQUIRED_DATASET_FILES: tuple[str, ...] = (
    "accession_records.json",
    "curator_notes.md",
    "property_ledger_1908.txt",
    "photograph_catalog.json",
)
"""tuple[str, ...]: Filenames that must be present in the datasets directory."""

DOCUMENT_TYPE_BY_SUFFIX: dict[str, str] = {
    ".json": "json",
    ".md": "markdown",
    ".txt": "text",
}
"""dict[str, str]: Mapping from file suffix to normalized document type label."""


class DatasetService:
    """Load, validate, and persist demo datasets into SQLite.

    :ivar Path _datasets_path: Root directory containing required demo dataset files.
    :ivar sessionmaker[Session] _session_factory: Factory for transactional database sessions.
    """

    def __init__(
        self,
        datasets_path: Path,
        session_factory: sessionmaker[Session],
    ) -> None:
        """Initialize the dataset service.

        :param Path datasets_path: Directory containing required demo dataset files.
        :param sessionmaker[Session] session_factory: Factory used to persist
            documents and records.
        :returns: None
        :rtype: None
        """
        self._datasets_path = datasets_path
        self._session_factory = session_factory

    async def load_dataset(self) -> list[Document]:
        """Parse required dataset assets and persist them when the store is empty.

        The blocking ingestion lifecycle is offloaded to a worker thread so file
        reads and SQLite writes do not block the FastAPI event loop.

        :returns: Persisted or existing source document rows for each dataset file.
        :rtype: list[Document]
        :raises DatasetFileNotFoundError: If any required dataset file is missing.
        :raises DatasetEncodingError: If a dataset file cannot be decoded as UTF-8.
        :raises DatasetSchemaError: If a dataset file violates its expected schema.
        :raises DatasetValidationError: If a JSON row fails Pydantic validation.
        """
        return await asyncio.to_thread(self.initialize_datasets)

    def initialize_datasets(self) -> list[Document]:
        """Run the dataset ingestion lifecycle synchronously on a worker thread.

        Checks for existing documents, then reads, validates, and persists each
        required dataset file when the memory store is empty.

        :returns: Persisted or existing source document rows for each dataset file.
        :rtype: list[Document]
        :raises DatasetFileNotFoundError: If any required dataset file is missing.
        :raises DatasetEncodingError: If a dataset file cannot be decoded as UTF-8.
        :raises DatasetSchemaError: If a dataset file violates its expected schema.
        :raises DatasetValidationError: If a JSON row fails Pydantic validation.
        """
        self._ensure_required_files()

        if self._database_has_documents():
            return self._load_existing_documents()

        return [self._ingest_file_sync(filename) for filename in REQUIRED_DATASET_FILES]

    def _database_has_documents(self) -> bool:
        """Return whether the memory store already contains ingested documents.

        :returns: ``True`` when one or more document rows exist, else ``False``.
        :rtype: bool
        """
        with self._session_factory() as session:
            document_count = session.scalar(select(func.count()).select_from(Document)) or 0
            return document_count > 0

    def _load_existing_documents(self) -> list[Document]:
        """Load persisted source documents without re-ingesting dataset files.

        Eager-loads child records and expunges hydrated instances so relationship
        pointers remain valid after the session context closes.

        :returns: All document rows currently stored in the database.
        :rtype: list[Document]
        """
        with self._session_factory() as session:
            documents = list(
                session.scalars(
                    select(Document).options(joinedload(Document.records))
                )
                .unique()
                .all()
            )
            for document in documents:
                for record in document.records:
                    session.expunge(record)
                session.expunge(document)
            return documents

    def load_record(
        self,
        session: Session,
        document: Document,
        record_payload: dict[str, Any],
    ) -> Record:
        """Persist a validated semantic record linked to a source document.

        :param Session session: Active database session for the insert.
        :param Document document: Parent source document for the record.
        :param dict[str, Any] record_payload: Normalized record fields including
            ``id``, ``title``, ``content``, ``classification``, ``confidence``,
            and ``provenance``.
        :returns: Newly created, session-attached record row.
        :rtype: Record
        """
        record = Record(
            id=record_payload["id"],
            document_id=document.id,
            title=record_payload["title"],
            content=record_payload["content"],
            classification=record_payload["classification"],
            confidence=float(record_payload["confidence"]),
            provenance_json=json.dumps(record_payload["provenance"]),
            created_at=datetime.now(UTC).isoformat(),
        )
        session.add(record)
        return record

    def validate_record(
        self,
        path: Path,
        schema_name: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Coerce and validate a single record payload against a known schema.

        :param Path path: Filesystem path to the dataset file containing the row.
        :param str schema_name: Schema key (``accession`` or ``photograph``).
        :param dict[str, Any] payload: Raw JSON object to validate.
        :returns: Validated and coerced record fields as a plain dictionary.
        :rtype: dict[str, Any]
        :raises DatasetValidationError: If Pydantic validation fails.
        :raises DatasetSchemaError: If ``schema_name`` is not recognized.
        """
        try:
            if schema_name == "accession":
                model = AccessionRecordSchema.model_validate(payload)
                return model.model_dump()
            if schema_name == "photograph":
                model = PhotographRecordSchema.model_validate(payload)
                return model.model_dump()
        except ValidationError as exc:
            raise DatasetValidationError(path, str(exc)) from exc

        raise DatasetSchemaError(path, f"Unknown record schema: {schema_name}")

    def _ensure_required_files(self) -> None:
        """Fail fast when any required dataset asset is missing.

        :returns: None
        :rtype: None
        :raises DatasetFileNotFoundError: If a required dataset file is absent.
        """
        for filename in REQUIRED_DATASET_FILES:
            path = self._datasets_path / filename
            if not path.is_file():
                raise DatasetFileNotFoundError(path)

    def _ingest_file_sync(self, filename: str) -> Document:
        """Read, validate, and persist a single dataset file synchronously.

        :param str filename: Name of the dataset file within ``datasets_path``.
        :returns: Persisted source document row with associated records, expunged
            from the session so relationship pointers remain valid after return.
        :rtype: Document
        :raises DatasetEncodingError: If the file is empty or not valid UTF-8.
        :raises DatasetSchemaError: If the file extension or contents are invalid.
        :raises DatasetValidationError: If JSON rows fail schema validation.
        """
        path = self._datasets_path / filename
        raw_bytes = path.read_bytes()
        decoded_text = self._decode_utf8(path, raw_bytes)
        sanitized_text = strip_author_footers(decoded_text)
        suffix = path.suffix.lower()
        document_type = DOCUMENT_TYPE_BY_SUFFIX.get(suffix)
        if document_type is None:
            raise DatasetSchemaError(path, f"Unsupported file extension: {suffix}")

        with self._session_factory() as session:
            document = self._persist_document(session, filename, document_type, sanitized_text)
            if document_type == "json":
                self._ingest_json_records(session, path, document, sanitized_text)
            else:
                self._ingest_text_record(session, path, document, sanitized_text)
            session.commit()
            session.refresh(document)
            for record in document.records:
                session.expunge(record)
            session.expunge(document)

        return document

    def _decode_utf8(self, path: Path, raw_bytes: bytes) -> str:
        """Decode dataset bytes using strict UTF-8 validation.

        :param Path path: Filesystem path to the dataset file being decoded.
        :param bytes raw_bytes: Raw file contents read from disk.
        :returns: UTF-8 decoded text content.
        :rtype: str
        :raises DatasetEncodingError: If the file is empty or decoding fails.
        """
        if not raw_bytes:
            raise DatasetEncodingError(path, "File is empty")
        try:
            return raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DatasetEncodingError(path, str(exc)) from exc

    def _persist_document(
        self,
        session: Session,
        filename: str,
        document_type: str,
        content: str,
    ) -> Document:
        """Create or replace a source document row for the given file.

        :param Session session: Active database session for the upsert.
        :param str filename: Original dataset filename.
        :param str document_type: Normalized document type label.
        :param str content: Full decoded file contents.
        :returns: Newly created document row flushed to the session.
        :rtype: Document
        """
        document_id = f"doc-{Path(filename).stem}"
        existing = session.get(Document, document_id)
        if existing is not None:
            session.delete(existing)
            session.flush()

        document = Document(
            id=document_id,
            filename=filename,
            document_type=document_type,
            content=content,
            created_at=datetime.now(UTC).isoformat(),
        )
        session.add(document)
        session.flush()
        return document

    def _ingest_json_records(
        self,
        session: Session,
        path: Path,
        document: Document,
        text: str,
    ) -> None:
        """Parse JSON array datasets into normalized record rows.

        :param Session session: Active database session for record inserts.
        :param Path path: Filesystem path to the JSON dataset file.
        :param Document document: Parent document row for generated records.
        :param str text: Decoded JSON file contents.
        :returns: None
        :rtype: None
        :raises DatasetSchemaError: If JSON is malformed, empty, or unsupported.
        :raises DatasetValidationError: If individual rows fail validation.
        """
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DatasetSchemaError(path, f"Invalid JSON: {exc}") from exc

        if not isinstance(payload, list) or not payload:
            raise DatasetSchemaError(path, "JSON dataset must be a non-empty array")

        if path.name == "accession_records.json":
            for item in payload:
                if not isinstance(item, dict):
                    raise DatasetSchemaError(path, "Each accession row must be an object")
                validated = self.validate_record(path, "accession", item)
                record_payload = {
                    "id": f"record-{validated['accession_number']}",
                    "title": validated["title"],
                    "content": (
                        f"Accession {validated['accession_number']} acquired on "
                        f"{validated['date_acquired']} from {validated['source']}."
                    ),
                    "classification": "accession",
                    "confidence": validated["confidence"],
                    "provenance": {
                        "source_file": path.name,
                        "accession_number": validated["accession_number"],
                    },
                }
                self.load_record(session, document, record_payload)
            return

        if path.name == "photograph_catalog.json":
            for item in payload:
                if not isinstance(item, dict):
                    raise DatasetSchemaError(path, "Each photograph row must be an object")
                validated = self.validate_record(path, "photograph", item)
                subjects = ", ".join(validated["subjects"])
                record_payload = {
                    "id": f"record-{validated['photo_id']}",
                    "title": validated["caption"],
                    "content": (
                        f"Photograph {validated['photo_id']} ({validated['estimated_year']}): "
                        f"{validated['caption']}. Subjects: {subjects}."
                    ),
                    "classification": "photograph",
                    "confidence": 0.95,
                    "provenance": {
                        "source_file": path.name,
                        "photo_id": validated["photo_id"],
                    },
                }
                self.load_record(session, document, record_payload)
            return

        raise DatasetSchemaError(path, f"Unsupported JSON dataset: {path.name}")

    def _ingest_text_record(
        self,
        session: Session,
        path: Path,
        document: Document,
        text: str,
    ) -> None:
        """Normalize markdown or plain-text datasets into a single record.

        :param Session session: Active database session for the record insert.
        :param Path path: Filesystem path to the text dataset file.
        :param Document document: Parent document row for the generated record.
        :param str text: Decoded file contents.
        :returns: None
        :rtype: None
        :raises DatasetSchemaError: If the text content is empty after stripping.
        """
        stripped = text.strip()
        if not stripped:
            raise DatasetSchemaError(path, "Text dataset must contain non-whitespace content")

        if path.suffix.lower() == ".md":
            classification = "curator_notes"
            title = "Curator Notes"
            record_id = "record-curator-notes"
        else:
            classification = "property_ledger"
            title = "Miller Household Property Ledger 1908"
            record_id = "record-property-ledger-1908"

        record_payload = {
            "id": record_id,
            "title": title,
            "content": stripped,
            "classification": classification,
            "confidence": 0.92,
            "provenance": {"source_file": path.name},
        }
        self.load_record(session, document, record_payload)

    def count_persisted_records(self) -> int:
        """Return the number of records currently stored in the database.

        :returns: Total count of rows in the ``records`` table.
        :rtype: int
        """
        with self._session_factory() as session:
            return session.scalar(select(func.count()).select_from(Record)) or 0
