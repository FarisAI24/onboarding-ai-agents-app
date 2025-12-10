"""Main FastAPI application for the Enterprise Onboarding Copilot."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import get_settings
from app.database import engine, Base
from app.api.routes import router
from app.api.auth_routes import router as auth_router
from app.api.middleware import SecurityMiddleware, MetricsMiddleware
from app.audit.middleware import AuditMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up Enterprise Onboarding Copilot")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Initialize hybrid search index if needed
    try:
        from rag.hybrid_search import get_hybrid_search_engine
        engine_hs = get_hybrid_search_engine()
        logger.info("Hybrid search engine initialized")
    except Exception as e:
        logger.warning(f"Could not initialize hybrid search: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enterprise Onboarding Copilot")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="""
    # Enterprise Onboarding Copilot
    
    A production-grade, multi-agent AI assistant for employee onboarding.
    
    ## Features
    
    - **🤖 Chat Assistant**: Ask questions about company policies (HR, IT, Security, Finance)
    - **📋 Task Management**: View and update onboarding tasks
    - **📊 Progress Tracking**: Monitor onboarding completion
    - **❓ FAQ Shortcuts**: Quick access to common questions
    - **👩‍💼 Admin Dashboard**: View aggregate metrics and user progress
    
    ## AI/ML Components
    
    - **Multi-Agent Architecture**: Specialized agents for each department
    - **Hybrid RAG**: Semantic + BM25 keyword search with reranking
    - **ML Routing**: Classical ML model for query classification
    - **Conversation Memory**: Context-aware responses
    
    ## Security
    
    - **Authentication**: JWT-based auth with access/refresh tokens
    - **RBAC**: Role-based access control with granular permissions
    - **Session Management**: User session tracking and caching
    - **PII Detection**: Automatic detection and redaction
    - **Rate Limiting**: Tiered rate limits by user type
    - **Audit Logging**: Comprehensive audit trail for all actions
    
    ## Monitoring
    
    - **Prometheus Metrics**: `/api/v1/metrics`
    - **Dashboard Metrics**: `/api/v1/dashboard/metrics`
    - **Health Check**: `/api/v1/health`
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware (rate limiting, headers)
app.add_middleware(SecurityMiddleware)

# Add metrics middleware (active request tracking)
app.add_middleware(MetricsMiddleware)

# Add audit middleware (request/response logging)
app.add_middleware(AuditMiddleware)

# Include API routes
app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "description": "Enterprise Onboarding Copilot - Production Grade",
        "docs": "/docs",
        "health": "/api/v1/health",
        "metrics": "/api/v1/metrics",
        "features": [
            "Multi-agent RAG system",
            "Hybrid search (semantic + BM25)",
            "ML-powered query routing",
            "Conversation memory",
            "Task recommendations",
            "JWT authentication & RBAC",
            "Session management",
            "PII detection & redaction",
            "Comprehensive audit logging",
            "Prometheus metrics"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
