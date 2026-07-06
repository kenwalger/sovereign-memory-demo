"""Fail-fast dataset ingestion for the institutional memory demo."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

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

DOCUMENT_TYPE_BY_SUFFIX: dict[str, str] = {
    ".json": "json",
    ".md": "markdown",
    ".txt": "text",
}


class DatasetService:
    """Load, validate, and persist demo datasets into SQLite."""

    def __init__(
        self,
        datasets_path: Path,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._datasets_path = datasets_path
        self._session_factory = session_factory

    async def load_dataset(self) -> list[Document]:
        """Parse all required dataset assets and persist them to the database."""
        self._ensure_required_files()

        documents: list[Document] = []
        for filename in REQUIRED_DATASET_FILES:
            document = await self._ingest_file(filename)
            documents.append(document)

        return documents

    def load_record(
        self,
        session: Session,
        document: Document,
        record_payload: dict[str, Any],
    ) -> Record:
        """Persist a validated semantic record linked to a source document."""
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
        """Coerce and validate a single record payload against a known schema."""
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
        """Fail fast when any required dataset asset is missing."""
        for filename in REQUIRED_DATASET_FILES:
            path = self._datasets_path / filename
            if not path.is_file():
                raise DatasetFileNotFoundError(path)

    async def _ingest_file(self, filename: str) -> Document:
        """Read, validate, and persist a single dataset file."""
        path = self._datasets_path / filename
        raw_bytes = await asyncio.to_thread(path.read_bytes)
        text = self._decode_utf8(path, raw_bytes)
        suffix = path.suffix.lower()
        document_type = DOCUMENT_TYPE_BY_SUFFIX.get(suffix)
        if document_type is None:
            raise DatasetSchemaError(path, f"Unsupported file extension: {suffix}")

        with self._session_factory() as session:
            document = self._persist_document(session, filename, document_type, text)
            if document_type == "json":
                self._ingest_json_records(session, path, document, text)
            else:
                self._ingest_text_record(session, path, document, text)
            session.commit()
            session.refresh(document)

        return document

    def _decode_utf8(self, path: Path, raw_bytes: bytes) -> str:
        """Decode dataset bytes using strict UTF-8 validation."""
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
        """Create or replace a source document row for the given file."""
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
        """Parse JSON array datasets into normalized record rows."""
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
        """Normalize markdown or plain-text datasets into a single record."""
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
        """Return the number of records currently stored in the database."""
        with self._session_factory() as session:
            return len(session.scalars(select(Record)).all())
