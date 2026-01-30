"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .websocket import websocket_endpoint


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AutoClaude UI",
        description="Web interface for monitoring and controlling AutoClaude",
        version="0.1.0",
    )

    # Configure CORS for local network access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for local network
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    # WebSocket endpoint
    app.websocket("/ws")(websocket_endpoint)

    @app.get("/")
    async def root():
        """Root endpoint - health check."""
        return {"status": "ok", "service": "autoclaude-ui"}

    return app
