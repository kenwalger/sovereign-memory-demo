"""Typed initialization errors raised during dataset ingestion."""

from pathlib import Path


class DatasetInitializationError(Exception):
    """Base error for dataset startup failures.

    All dataset ingestion errors inherit from this type so callers can catch
    initialization failures with a single exception handler.
    """


class DatasetFileNotFoundError(DatasetInitializationError):
    """Raised when a required dataset asset is missing.

    :ivar Path path: Filesystem path to the missing dataset file.
    """

    def __init__(self, path: Path) -> None:
        """Initialize a file-not-found dataset error.

        :param Path path: Filesystem path to the missing dataset asset.
        :returns: None
        :rtype: None
        """
        self.path = path
        super().__init__(f"Required dataset file not found: {path}")


class DatasetEncodingError(DatasetInitializationError):
    """Raised when a dataset file cannot be decoded as UTF-8.

    :ivar Path path: Filesystem path to the dataset file that failed decoding.
    :ivar str detail: Human-readable description of the encoding failure.
    """

    def __init__(self, path: Path, detail: str) -> None:
        """Initialize a dataset encoding error.

        :param Path path: Filesystem path to the dataset file that failed decoding.
        :param str detail: Human-readable description of the encoding failure.
        :returns: None
        :rtype: None
        """
        self.path = path
        self.detail = detail
        super().__init__(f"Dataset encoding error in {path.name}: {detail}")


class DatasetSchemaError(DatasetInitializationError):
    """Raised when a dataset file violates its expected schema.

    :ivar Path path: Filesystem path to the dataset file with schema violations.
    :ivar str detail: Human-readable description of the schema violation.
    """

    def __init__(self, path: Path, detail: str) -> None:
        """Initialize a dataset schema error.

        :param Path path: Filesystem path to the dataset file with schema violations.
        :param str detail: Human-readable description of the schema violation.
        :returns: None
        :rtype: None
        """
        self.path = path
        self.detail = detail
        super().__init__(f"Dataset schema error in {path.name}: {detail}")


class DatasetValidationError(DatasetInitializationError):
    """Raised when coerced dataset values fail range or type checks.

    :ivar Path path: Filesystem path to the dataset file with invalid values.
    :ivar str detail: Human-readable description of the validation failure.
    """

    def __init__(self, path: Path, detail: str) -> None:
        """Initialize a dataset validation error.

        :param Path path: Filesystem path to the dataset file with invalid values.
        :param str detail: Human-readable description of the validation failure.
        :returns: None
        :rtype: None
        """
        self.path = path
        self.detail = detail
        super().__init__(f"Dataset validation error in {path.name}: {detail}")


class ReceiptServiceError(Exception):
    """Base error for forensic receipt generation failures.

    All receipt service errors inherit from this type so callers can catch
    receipt workflow failures with a single exception handler.
    """


class ReceiptValidationError(ReceiptServiceError):
    """Raised when receipt inputs fail validation.

    :ivar str detail: Human-readable description of the validation failure.
    """

    def __init__(self, detail: str) -> None:
        """Initialize a receipt validation error.

        :param str detail: Human-readable description of the validation failure.
        :returns: None
        :rtype: None
        """
        self.detail = detail
        super().__init__(detail)


class ReceiptDuplicateError(ReceiptServiceError):
    """Raised when a receipt payload hash already exists in storage.

    :ivar str payload_hash: Deterministic hash that collided with an existing receipt.
    """

    def __init__(self, payload_hash: str) -> None:
        """Initialize a duplicate receipt error.

        :param str payload_hash: Deterministic hash that collided with an existing receipt.
        :returns: None
        :rtype: None
        """
        self.payload_hash = payload_hash
        super().__init__(f"Receipt payload hash already exists: {payload_hash}")
