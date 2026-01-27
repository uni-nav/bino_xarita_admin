

# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api import floors, waypoints, navigation, rooms, kiosks
from app.core.config import settings

app = FastAPI(title="University Navigation API", version="1.0.0")

# CORS - configured origins only (no wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,  # ✅ Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Uploads papkani yaratish
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# API routes
app.include_router(floors.router, prefix="/api/floors", tags=["floors"])
app.include_router(waypoints.router, prefix="/api/waypoints", tags=["waypoints"])
app.include_router(navigation.router, prefix="/api/navigation", tags=["navigation"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["rooms"])
app.include_router(kiosks.router, prefix="/api/kiosks", tags=["kiosks"])

@app.get("/")
def root():
    return {"message": "University Navigation API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
