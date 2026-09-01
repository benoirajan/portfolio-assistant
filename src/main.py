import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.api.auth import router as auth_router
from src.api.holdings import router as holdings_router
from src.api.analytics import router as analytics_router

app = FastAPI(
    title="Portfolio Assistant API",
    description="Zerodha KiteConnect Integrated Portfolio Management & AI Advisory Backend",
    version="1.0.0"
)

# CORS middleware for local frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(holdings_router)
app.include_router(analytics_router)

@app.get("/")
def root():
    return {
        "app": "Portfolio Assistant API",
        "status": "online",
        "demo_mode": settings.DEMO_MODE,
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("src.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
