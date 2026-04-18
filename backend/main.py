"""
GuardianAI — Autonomous Emergency Response System
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routes import auth_routes, emergency_routes, guardian_routes, incident_routes, ws_routes

# ─── App Setup ───
app = FastAPI(
    title="GuardianAI",
    description="Autonomous Emergency Response System — AI-powered emergency detection, risk assessment, and response coordination.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───
app.include_router(auth_routes.router)
app.include_router(emergency_routes.router)
app.include_router(guardian_routes.router)
app.include_router(incident_routes.router)
app.include_router(ws_routes.router)


# ─── Startup ───
@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    print("")
    print("=" * 60)
    print("  GuardianAI - Autonomous Emergency Response System")
    print("=" * 60)
    print("Initializing database...")
    init_db()
    print("[OK] Database ready")
    print("[OK] AI Agents loaded (Intent, Risk, Location, Decision)")
    print("[OK] WebSocket server ready")
    print("[OK] API Docs: http://localhost:8000/docs")
    print("=" * 60)
    print("")


# ─── Health Check ───
@app.get("/", tags=["Health"])
def root():
    return {
        "name": "GuardianAI",
        "version": "1.0.0",
        "status": "operational",
        "agents": ["IntentAgent", "RiskAgent", "LocationAgent", "DecisionEngine"],
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
