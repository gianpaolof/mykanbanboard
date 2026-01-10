"""FastAPI main application for Kanban AI agent."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import dspy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# LIFESPAN CONTEXT MANAGER
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and cleanup resources on app startup/shutdown.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info("Starting Kanban AI Agent...")
    logger.info(f"Using model: {settings.default_model}")

    try:
        # Initialize DSPy with Claude
        setup_dspy()
        logger.info("DSPy initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize DSPy: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Kanban AI Agent...")


# ============================================================================
# DSPY SETUP
# ============================================================================


def setup_dspy() -> None:
    """Configure DSPy with Claude as the language model.

    This sets up the global DSPy configuration to use Claude Sonnet
    as the primary language model for all DSPy modules.

    Raises:
        ValueError: If API key is not configured
        Exception: If model initialization fails
    """
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is required")

    try:
        # Configure Claude as the LM
        lm = dspy.LM(
            model=f"anthropic/{settings.default_model}",
            api_key=settings.anthropic_api_key,
            temperature=0.7,
            max_tokens=2048,
        )

        # Set as default LM
        dspy.configure(lm=lm)

        logger.info(f"DSPy configured with {settings.default_model}")

    except Exception as e:
        logger.error(f"Failed to setup DSPy: {str(e)}")

        # Try fallback to OpenAI if configured
        if settings.openai_api_key:
            logger.info(f"Trying fallback model: {settings.fallback_model}")
            try:
                lm = dspy.LM(
                    model=f"openai/{settings.fallback_model}",
                    api_key=settings.openai_api_key,
                    temperature=0.7,
                    max_tokens=2048,
                )
                dspy.configure(lm=lm)
                logger.info(f"Using fallback model: {settings.fallback_model}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                raise
        else:
            raise


# ============================================================================
# FASTAPI APP
# ============================================================================


app = FastAPI(
    title="Kanban AI Agent",
    description="DSPy-based AI agent for intelligent task management",
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================================
# CORS MIDDLEWARE
# ============================================================================


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "tauri://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================


app.include_router(router)


# ============================================================================
# ROOT ENDPOINT
# ============================================================================


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with service info.

    Returns:
        Service information
    """
    return {
        "service": "Kanban AI Agent",
        "version": "0.1.0",
        "status": "running",
        "model": settings.default_model,
    }


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions.

    Args:
        request: Request object
        exc: Exception

    Returns:
        Error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.debug else None,
        },
    )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
