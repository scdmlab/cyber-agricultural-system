from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import pandas as pd
from pathlib import Path as FilePath
import os
from pydantic import BaseModel, Field
from typing import List
from enum import Enum
from fastapi.params import Path

from routers import model, prediction, health

app = FastAPI(
    title="Crop Yield Prediction API",
    description="""
    This API provides crop yield predictions and historical data for corn and soybean crops.
    It offers both end-of-season and in-season predictions based on various environmental and agricultural features.
    
    Key Features:
    - Crop yield predictions using machine learning models
    - Historical yield data access
    - Geographic data integration
    - Real-time feature extraction from GeoJSON input
    """,
    version="1.0.0",
    contact={
        "name": "SCDMlab @ UW-Madison",
        "email": "",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(model.router, tags=["Model"])
app.include_router(prediction.router, tags=["Predictions"])

# Data directory configuration
BASE_DIR = FilePath(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RESULT_DIR = BASE_DIR / "result_corn"
RESULT_SOYBEAN_DIR = BASE_DIR / "result_soybean"

class CropType(str, Enum):
    corn = "corn"
    soybean = "soybean"

class PredictionRecord(BaseModel):
    FIPS: int = Field(..., description="County FIPS code", example=55013)
    y_test_pred: float = Field(..., description="Predicted yield", example=45.8)
    y_test: float = Field(..., description="Actual yield", example=45.8)
    y_test_pred_uncertainty: float = Field(..., description="Prediction uncertainty", example=0.79)

@app.get("/api/data/{crop}/{year}/{month}.json", include_in_schema=False)
async def get_map_data(crop: str, year: str, month: str):
    try:
        file_path = DATA_DIR / crop / year / f"{month}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Data not found: {file_path}")
        return file_path.read_text()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/corn_yield_US.csv", include_in_schema=False)
async def get_historical_data():
    try:
        file_path = DATA_DIR / "corn_yield_US.csv"
        df = pd.read_csv(file_path)
        df = df.replace([float('inf'), float('-inf')], None)
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/average_pred.csv", include_in_schema=False)
async def get_average_pred():
    try:
        file_path = DATA_DIR / "average_pred.csv"
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/county.csv", include_in_schema=False)
async def get_county_data():
    try:
        file_path = DATA_DIR / "county.csv"
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/county_info.csv", include_in_schema=False)
async def get_county_info():
    try:
        file_path = DATA_DIR / "county_info.csv"
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/predictions/{crop}/{year}",
    summary="Get All County Predictions",
    description="""
    Retrieves crop yield predictions for all counties for a specific crop and year.
    
    The response includes:
    - FIPS code for each county
    - Predicted yield
    - Actual yield
    - Prediction uncertainty
    """,
    response_model=List[PredictionRecord],
    responses={
        200: {
            "description": "Successful retrieval of predictions",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "FIPS": 55013,
                            "y_test_pred": 45.8,
                            "y_test": 45.8,
                            "y_test_pred_uncertainty": 0.79
                        },
                        {
                            "FIPS": 27097,
                            "y_test_pred": 51.0,
                            "y_test": 51.0,
                            "y_test_pred_uncertainty": 0.78
                        }
                    ]
                }
            }
        },
        404: {
            "description": "Predictions not found",
            "content": {
                "application/json": {
                    "example": {"detail": "No predictions found for specified crop and year"}
                }
            }
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error reading prediction file"}
                }
            }
        }
    }
)
async def get_predictions(
    crop: CropType = Path(..., description="Type of crop (corn or soybean)"),
    year: str = Path(..., description="Prediction year (e.g., 2024)", regex="^20\d{2}$")
):
    try:
        base_dir = RESULT_SOYBEAN_DIR if crop == "soybean" else RESULT_DIR
        file_path = base_dir / "bnn" / f"result{year}.csv"
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve data files
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")
app.mount("/result_corn", StaticFiles(directory=str(RESULT_DIR)), name="result_corn")
app.mount("/result_soybean", StaticFiles(directory=str(RESULT_SOYBEAN_DIR)), name="result_soybean")

# Only serve the Vue app in production
if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi 