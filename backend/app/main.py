from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.security import hash_password
from app.models import *  # Import all models to ensure metadata is populated
from app.api.v1 import auth, profile, resumes, jobs, recommendations, applications
from sqlalchemy import select

FRONTEND_INDEX = Path(__file__).resolve().parent.parent.parent / "frontend" / "index.html"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed Default Enterprise Administrator if not exists
    async with AsyncSessionLocal() as db:
        admin_res = await db.execute(select(User).where(User.email == "admin@careerradar.ai"))
        if not admin_res.scalar_one_or_none():
            admin_user = User(
                email="admin@careerradar.ai",
                hashed_password=hash_password("AdminPassword2026!"),
                role="admin",
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            await db.flush()
            admin_prof = UserProfile(
                user_id=admin_user.id,
                full_name="System Administrator",
                headline="Platform Operations & ATS Engineering Admin"
            )
            db.add(admin_prof)
            await db.commit()

    yield
    # Teardown
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="CareerRadar AI: Intelligent Job Discovery, Multi-Resume Intelligence & Career Recommendation Engine",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(resumes.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)
app.include_router(applications.router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Frontend"])
async def serve_frontend():
    if FRONTEND_INDEX.exists():
        return FileResponse(str(FRONTEND_INDEX))
    return {"message": "CareerRadar AI Backend Active", "docs": "/docs"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": "production-ready"
    }
