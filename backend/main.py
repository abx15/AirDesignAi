import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

from routes import auth, equations, solve
from schemas import HealthResponse
from database import init_db
from utils.logging_config import setup_logging
from utils.security import setup_rate_limiting, limiter


def get_cors_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


# Initialize logging
setup_logging()

app = FastAPI(title="MotionMath AI Gesture Solver", version="1.0.0")

# Setup Rate Limiting
setup_rate_limiting(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(equations.router)
app.include_router(solve.router)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


@app.get("/health", tags=["system"], response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.utcnow())

