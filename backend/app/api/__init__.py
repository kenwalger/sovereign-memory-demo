"""HTTP route handlers for the Sovereign Memory Demo API.

Re-exports the API router mounted by the FastAPI application entrypoint.
"""

from app.api.routes import router

__all__ = ["router"]
