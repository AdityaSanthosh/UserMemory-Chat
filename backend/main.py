import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import router as auth_router
from .chat import router as chat_router
from .database import close_mongo, init_db, init_mongo

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    await init_db()
    await init_mongo()
    yield
    # Shutdown
    await close_mongo()


app = FastAPI(
    title="Gemini Chat API",
    description="A chat application with Gemini-like UX using Google ADK",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
# Allow both development (localhost) and production (Vercel) origins
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add production frontend URL from environment variable
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
