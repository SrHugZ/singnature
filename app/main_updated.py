from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from contextlib import asynccontextmanager
import traceback
import logging

from app.core.config import settings
from app.db.session import test_db_connection
from app.db.redis_client import test_redis_connection

# Import routers
from app.api.v1 import auth, organizations, members

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the application"""
    # Startup
    print("🚀 Starting application...")
    logger.info("Application starting...")
    yield
    # Shutdown
    print("🛑 Shutting down application...")
    logger.info("Application shutting down...")


app = FastAPI(
    title="Signatures Platform API",
    description="Dynamic Email Signatures & Banners Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware - DEVE ser adicionado ANTES de tudo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Middleware para adicionar CORS headers em TODAS as respostas
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    try:
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error in middleware: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(e)},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )


# Exception handler para ResponseValidationError (erro de validação na resposta)
@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
    """
    Handler para erros de validação da resposta
    """
    logger.error(f"Response validation error: {exc.errors()}")
    logger.error(f"Body causing error: {exc.body}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Response validation error",
            "errors": exc.errors() if settings.DEBUG else "Internal server error"
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


# Exception handler para RequestValidationError (erro de validação na requisição)
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler para erros de validação da requisição
    """
    logger.error(f"Request validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation error",
            "errors": exc.errors()
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


# Exception handler global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global para capturar exceções e garantir que os headers CORS sejam incluídos
    """
    logger.error(f"Global exception handler caught: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An error occurred"
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint that verifies database and Redis connections.
    Returns 200 OK if all services are healthy, 503 Service Unavailable otherwise.
    """
    status_check = {
        "status": "ok",
        "database": "unknown",
        "redis": "unknown"
    }
    
    try:
        # Test database connection
        test_db_connection()
        status_check["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        status_check["database"] = f"error: {str(e)}"
        status_check["status"] = "error"
    
    try:
        # Test Redis connection
        test_redis_connection()
        status_check["redis"] = "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        status_check["redis"] = f"error: {str(e)}"
        status_check["status"] = "error"
    
    # Return 503 if any service is down
    if status_check["status"] == "error":
        return JSONResponse(status_code=503, content=status_check)
    
    return status_check


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Signatures Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])
app.include_router(members.router, prefix="/api/v1/members", tags=["Members"])