from fastapi import APIRouter, Response, status
from typing import Dict, List
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import psutil
import time
from datetime import datetime, timezone
import sys
import os

router = APIRouter(
    prefix="/api",
    tags=["Health"],
    responses={
        503: {
            "description": "Service Unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2024-03-20T10:00:00Z",
                        "error": "Service unavailable"
                    }
                }
            }
        }
    }
)

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

@router.get("/health",
    response_model=Dict,
    summary="Basic Health Check",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-03-20T10:00:00Z"
                    }
                }
            }
        }
    })
async def health_check(response: Response):
    """
    Basic health check endpoint that returns service status.
    
    Returns:
        - status: Current health status of the service ("healthy" or "unhealthy")
        - timestamp: UTC timestamp of the health check
    
    Raises:
        - 503: Service Unavailable if health check fails
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

@router.get("/health/detailed",
    response_model=Dict,
    summary="Detailed Health Check",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Detailed system health information",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-03-20T10:00:00Z",
                        "uptime": "10 days, 4:12:33",
                        "system": {
                            "cpu": {
                                "usage_percent": 45.2,
                                "cores": 8
                            },
                            "memory": {
                                "total": 16777216000,
                                "available": 8388608000,
                                "used_percent": 50.0
                            },
                            "disk": {
                                "total": 250790436864,
                                "free": 125395218432,
                                "used_percent": 50.0
                            }
                        },
                        "environment": {
                            "python_version": "3.9.0",
                            "timezone": "UTC",
                            "hostname": "server-name"
                        }
                    }
                }
            }
        }
    })
async def detailed_health_check(response: Response):
    """
    Detailed health check including system metrics, uptime, and environment info.
    
    Returns:
        - status: Current health status of the service ("healthy" or "unhealthy")
        - timestamp: UTC timestamp of the health check
        - uptime: System uptime in human-readable format
        - system: Detailed system metrics
            - cpu: CPU information (usage percentage and core count)
            - memory: Memory statistics (total, available, usage percentage)
            - disk: Disk usage information (total, free, usage percentage)
        - environment: Environment information
            - python_version: Current Python version
            - timezone: System timezone
            - hostname: System hostname
    
    Raises:
        - 503: Service Unavailable if health check fails, includes error message
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