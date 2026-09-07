import time
import uuid
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.core.logging_config import setup_logging
from src.core.config import settings
from src.api.auth import router as auth_router
from src.api.holdings import router as holdings_router
from src.api.analytics import router as analytics_router
from src.api.advisory import router as advisory_router

setup_logging(level="INFO")
logger = logging.getLogger("portfolio_assistant.main")

app = FastAPI(
    title="Portfolio Assistant API",
    description="Zerodha KiteConnect Integrated Portfolio Management & AI Advisory Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    logger.info("→ %s %s [req_id=%s]", request.method, request.url.path, request_id)
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "← %s %s [req_id=%s] status=%d %.1fms",
            request.method, request.url.path, request_id, response.status_code, elapsed_ms
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error(
            "✗ %s %s [req_id=%s] UNHANDLED ERROR after %.1fms: %s",
            request.method, request.url.path, request_id, elapsed_ms, exc, exc_info=True
        )
        raise


app.include_router(auth_router)
app.include_router(holdings_router)
app.include_router(analytics_router)
app.include_router(advisory_router)


@app.get("/health")
def health():
    logger.debug("Health check called")
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "app": "Portfolio Assistant API",
        "status": "online",
        "demo_mode": settings.DEMO_MODE,
        "docs": "/docs"
    }


@app.on_event("startup")
async def on_startup():
    logger.info(
        "Portfolio Assistant API starting — demo_mode=%s host=%s port=%s",
        settings.DEMO_MODE, settings.APP_HOST, settings.APP_PORT
    )


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Portfolio Assistant API shutting down")


if __name__ == "__main__":
    uvicorn.run("src.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
