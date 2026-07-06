"""Typed initialization errors raised during dataset ingestion."""

from pathlib import Path


class DatasetInitializationError(Exception):
    """Base error for dataset startup failures."""


class DatasetFileNotFoundError(DatasetInitializationError):
    """Raised when a required dataset asset is missing."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Required dataset file not found: {path}")


class DatasetEncodingError(DatasetInitializationError):
    """Raised when a dataset file cannot be decoded as UTF-8."""

    def __init__(self, path: Path, detail: str) -> None:
        self.path = path
        self.detail = detail
        super().__init__(f"Dataset encoding error in {path.name}: {detail}")


class DatasetSchemaError(DatasetInitializationError):
    """Raised when a dataset file violates its expected schema."""

    def __init__(self, path: Path, detail: str) -> None:
        self.path = path
        self.detail = detail
        super().__init__(f"Dataset schema error in {path.name}: {detail}")


class DatasetValidationError(DatasetInitializationError):
    """Raised when coerced dataset values fail range or type checks."""

    def __init__(self, path: Path, detail: str) -> None:
        self.path = path
        self.detail = detail
        super().__init__(f"Dataset validation error in {path.name}: {detail}")


class ReceiptServiceError(Exception):
    """Base error for forensic receipt generation failures."""


class ReceiptValidationError(ReceiptServiceError):
    """Raised when receipt inputs fail validation."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class ReceiptDuplicateError(ReceiptServiceError):
    """Raised when a receipt payload hash already exists in storage."""

    def __init__(self, payload_hash: str) -> None:
        self.payload_hash = payload_hash
        super().__init__(f"Receipt payload hash already exists: {payload_hash}")
