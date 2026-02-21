"""
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routers import diagnosis, adversarial, trajectory, community

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

# Include routers
app.include_router(diagnosis.router, prefix=settings.API_V1_PREFIX)
app.include_router(adversarial.router, prefix=settings.API_V1_PREFIX)
app.include_router(trajectory.router, prefix=settings.API_V1_PREFIX)
app.include_router(community.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Neuro-Vitals API",
        "version": settings.VERSION,
        "docs": "/docs",
        "endpoints": {
            "diagnosis": f"{settings.API_V1_PREFIX}/diagnosis/analyze",
            "adversarial": f"{settings.API_V1_PREFIX}/adversarial/debate",
            "trajectory": f"{settings.API_V1_PREFIX}/trajectory/forecast",
            "community": f"{settings.API_V1_PREFIX}/community/heatmap"
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
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
