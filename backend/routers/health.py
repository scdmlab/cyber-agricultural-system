from fastapi import APIRouter, Response, status
from typing import Dict, List
import psutil
import time
from datetime import datetime, timezone
import sys
import os

router = APIRouter()

def get_system_health() -> Dict:
    """Get system health metrics"""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "cpu": {
            "usage_percent": psutil.cpu_percent(),
            "cores": psutil.cpu_count()
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "used_percent": memory.percent
        },
        "disk": {
            "total": disk.total,
            "free": disk.free,
            "used_percent": disk.percent
        }
    }

@router.get("/api/health",
    response_model=Dict,
    summary="Basic Health Check",
    status_code=status.HTTP_200_OK)
async def health_check(response: Response):
    """
    Basic health check endpoint that returns service status
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/api/health/detailed",
    response_model=Dict,
    summary="Detailed Health Check",
    status_code=status.HTTP_200_OK)
async def detailed_health_check(response: Response):
    """
    Detailed health check including system metrics, uptime, and environment info
    """
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        health_info = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": str(uptime),
            "system": get_system_health(),
            "environment": {
                "python_version": sys.version,
                "timezone": time.tzname[0],
                "hostname": os.uname().nodename if hasattr(os, 'uname') else None
            }
        }
        return health_info
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        } 