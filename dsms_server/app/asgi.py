"""ASGI application entry point"""
from app.config.server import server_config

# Setup startup and shutdown events
server_config.startup()
server_config.shutdown()

# Include API routes
from app.api import router as api_router
server_config.include_router(api_router, prefix="/api")

# Export the application
app = server_config.app
