from fastapi import APIRouter, Response
from typing import Dict
import psutil
import time

router = APIRouter()

@router.get("/api/health", 
    response_model=Dict[str, str],
    summary="Health Check",
    description="Returns the current status of the API service.")
async def health_check():
    """
    Performs a basic health check of the service.
    
    Returns:
        dict: Contains status information about the service
    """
    return {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@router.get("/api/health/detailed",
    summary="Detailed Health Check",
    description="Returns detailed system metrics and service status.")
async def detailed_health_check():
    """
    Performs a detailed health check including system metrics.
    
    Returns:
        dict: Contains detailed system metrics and status information
    """
    return {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system": {
            "cpu_usage": f"{psutil.cpu_percent()}%",
            "memory_usage": f"{psutil.virtual_memory().percent}%",
            "disk_usage": f"{psutil.disk_usage('/').percent}%"
        }
    } 