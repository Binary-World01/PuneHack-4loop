"""
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers.diagnosis import router as diagnosis_router
from app.routers.adversarial import router as adversarial_router
from app.routers.trajectory import router as trajectory_router
from app.routers.community import router as community_router
from app.routers.vitals import router as vitals_router
from app.routers.risk import router as risk_router
from app.routers.outbreak import router as outbreak_router

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Neuro-Vitals: Predictive Health Intelligence System"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with explicit global /api prefix
app.include_router(diagnosis_router, prefix="/api")
app.include_router(adversarial_router, prefix="/api")
app.include_router(trajectory_router, prefix="/api")
app.include_router(community_router, prefix="/api")
app.include_router(vitals_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(outbreak_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Neuro-Vitals API",
        "version": settings.VERSION,
        "docs": "/docs",
        "endpoints": {
            "diagnosis": "/api/diagnosis/analyze",
            "adversarial": "/api/adversarial/debate",
            "trajectory": "/api/trajectory/forecast",
            "community": "/api/community/heatmap",
            "vitals": {
                "save": "/api/save-vitals",
                "get": "/api/get-vitals/{user_email}",
                "latest": "/api/get-latest-vitals/{user_email}",
                "delete": "/api/delete-vitals/{user_email}",
                "health": "/api/vitals-health"
            },
            "risk": {
                "predict": "/api/risk/predict",
                "ocr": "/api/risk/ocr",
                "history": "/api/risk/history/{email}",
                "daily_log": "/api/risk/daily-log",
                "medical_record": "/api/risk/medical-record"
            },
            "outbreak": {
                "analyze": "/api/outbreak/analyze",
                "map": "/api/outbreak/map",
                "nearby": "/api/outbreak/map/nearby",
                "admin": "/api/outbreak/admin"
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )