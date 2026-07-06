"""Domain services for ingestion, retrieval, and receipt workflows.

Re-exports service classes and typed exceptions for dataset ingestion,
memory retrieval, and forensic receipt generation.
"""

from app.services.dataset_service import DatasetService
from app.services.exceptions import (
    DatasetEncodingError,
    DatasetFileNotFoundError,
    DatasetInitializationError,
    DatasetSchemaError,
    DatasetValidationError,
    ReceiptDuplicateError,
    ReceiptServiceError,
    ReceiptValidationError,
)
from app.services.memory_service import MemoryService, SourceAttribution
from app.services.receipt_service import ReceiptService

__all__ = [
    "DatasetEncodingError",
    "DatasetFileNotFoundError",
    "DatasetInitializationError",
    "DatasetSchemaError",
    "DatasetService",
    "DatasetValidationError",
    "MemoryService",
    "ReceiptDuplicateError",
    "ReceiptService",
    "ReceiptServiceError",
    "ReceiptValidationError",
    "SourceAttribution",
]
