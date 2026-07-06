"""FastAPI dependency providers for API route handlers."""

from fastapi import Request

from app.repositories.memory_repository import MemoryRepository
from app.services.memory_service import MemoryService
from app.services.receipt_service import ReceiptService


def get_memory_service(request: Request) -> MemoryService:
    """Return the application-scoped memory service.

    :param Request request: Incoming HTTP request carrying application state.
    :returns: Memory service initialized during application startup.
    :rtype: MemoryService
    """
    return request.app.state.memory_service


def get_receipt_service(request: Request) -> ReceiptService:
    """Return the application-scoped receipt service.

    :param Request request: Incoming HTTP request carrying application state.
    :returns: Receipt service initialized during application startup.
    :rtype: ReceiptService
    """
    return request.app.state.receipt_service


def get_memory_repository(request: Request) -> MemoryRepository:
    """Return the application-scoped memory repository.

    :param Request request: Incoming HTTP request carrying application state.
    :returns: Memory repository initialized during application startup.
    :rtype: MemoryRepository
    """
    return request.app.state.memory_repository
