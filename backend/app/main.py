from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import projects, ai, export
from app.core.config import settings
from app.core.database import init_db

app = FastAPI(
    title="MotionMath AI Backend",
    version="2.0.0",
    description="Architecture-focused CAD & Spatial Computing Engine"
)

# Set CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(export.router, prefix="/api/export", tags=["export"])

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "FastAPI 2.0"}
