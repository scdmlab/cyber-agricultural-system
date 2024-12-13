from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Optional, Union
from pathlib import Path as PathLib
import pandas as pd
from enum import Enum
import re

router = APIRouter(tags=["Predictions"])

BASE_DIR = PathLib(__file__).resolve().parent.parent
VALID_CROPS = ["corn", "soybean"]

# Define enums for validation
class CropType(str, Enum):
    corn = "corn"
    soybean = "soybean"

class PredictionType(str, Enum):
    end_of_season = "end_of_season"
    in_season = "in_season"

def get_all_prediction_files(crop: str, year: str) -> list[PathLib]:
    """Helper function to get all prediction files for a year"""
    result_dir = BASE_DIR / f"result_{crop}" / "bnn"
    return list(result_dir.glob(f"result{year}*.csv"))

# Define response models
class PredictionData(BaseModel):
    prediction: float = Field(..., description="Predicted crop yield in bushels per acre", example=45.8)
    actual: float = Field(..., description="Actual crop yield in bushels per acre", example=45.8)
    uncertainty: float = Field(..., description="Prediction uncertainty (standard deviation)", example=0.79)

class SinglePredictionResponse(BaseModel):
    crop: str = Field(..., description="Crop type (corn or soybean)", example="corn")
    year: str = Field(..., description="Prediction year", example="2024")
    fips: str = Field(..., description="County FIPS code", example="55013")
    prediction: float = Field(..., description="Predicted crop yield", example=45.8)
    actual: float = Field(..., description="Actual crop yield", example=45.8)
    uncertainty: float = Field(..., description="Prediction uncertainty", example=0.79)

class InSeasonPredictionResponse(BaseModel):
    crop: str = Field(..., description="Crop type (corn or soybean)", example="corn")
    year: str = Field(..., description="Prediction year", example="2024")
    fips: str = Field(..., description="County FIPS code", example="55013")
    predictions: Dict[str, PredictionData] = Field(
        ..., 
        description="Dictionary of predictions keyed by day of year",
        example={
            "180": {
                "prediction": 45.8,
                "actual": 45.8,
                "uncertainty": 0.79
            }
        }
    )

@router.get(
    "/api/predictions/{crop}/{year}/{prediction_type}/{fips}",
    summary="Get Crop Yield Predictions",
    description="""
    Retrieves crop yield predictions for a specific county (FIPS code).
    
    For end_of_season predictions, returns a single prediction for the entire season.
    For in_season predictions, returns multiple predictions throughout the growing season.
    
    The prediction values are in bushels per acre.
    Uncertainty is represented as one standard deviation.
    """,
    response_model=Union[SinglePredictionResponse, InSeasonPredictionResponse],
    responses={
        200: {
            "description": "Successful prediction retrieval",
            "content": {
                "application/json": {
                    "examples": {
                        "end_of_season": {
                            "summary": "End of Season Prediction",
                            "value": {
                                "crop": "corn",
                                "year": "2024",
                                "fips": "55013",
                                "prediction": 45.8,
                                "actual": 45.8,
                                "uncertainty": 0.79
                            }
                        },
                        "in_season": {
                            "summary": "In Season Predictions",
                            "value": {
                                "crop": "corn",
                                "year": "2024",
                                "fips": "55013",
                                "predictions": {
                                    "180": {
                                        "prediction": 45.8,
                                        "actual": 45.8,
                                        "uncertainty": 0.79
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_crop": {
                            "summary": "Invalid crop type",
                            "value": {"detail": "Invalid crop type"}
                        },
                        "invalid_fips": {
                            "summary": "Invalid FIPS code",
                            "value": {"detail": "Invalid FIPS code"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "examples": {
                        "no_predictions": {
                            "summary": "No predictions available",
                            "value": {"detail": "No predictions available for corn in 2024"}
                        },
                        "no_fips": {
                            "summary": "FIPS not found",
                            "value": {"detail": "No prediction found for FIPS 55013"}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Internal server error"}
                }
            }
        }
    }
)
async def get_predictions(
    crop: CropType = Path(..., description="Type of crop (corn or soybean)"),
    year: str = Path(..., description="Prediction year (e.g., 2024)", regex="^20\d{2}$"),
    prediction_type: PredictionType = Path(..., description="Type of prediction (end_of_season or in_season)"),
    fips: str = Path(..., description="County FIPS code", regex="^\d{5}$")
):
    """
    Get crop yield predictions for a specific FIPS code
    
    Parameters:
    - crop: corn or soybean
    - year: prediction year (e.g., 2024)
    - prediction_type: end_of_season or in_season
    - fips: county FIPS code
    """
    if crop.value not in VALID_CROPS:
        raise HTTPException(status_code=400, detail="Invalid crop type")
    
    try:
        result_dir = BASE_DIR / f"result_{crop.value}" / "bnn"
        
        if prediction_type == PredictionType.end_of_season:
            file_path = result_dir / f"result{year}.csv"
            if not file_path.exists():
                raise HTTPException(
                    status_code=404, 
                    detail=f"No predictions available for {crop.value} in {year}"
                )
            
            df = pd.read_csv(file_path)
            prediction = df[df['FIPS'] == int(fips)]
            
            if prediction.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No prediction found for FIPS {fips}"
                )
            
            return {
                "crop": crop.value,
                "year": year,
                "fips": fips,
                "prediction": float(prediction.iloc[0]['y_test_pred']),
                "actual": float(prediction.iloc[0]['y_test']),
                "uncertainty": float(prediction.iloc[0]['y_test_pred_uncertainty'])
            }
            
        else:  # in_season
            files = get_all_prediction_files(crop.value, year)
            if not files:
                raise HTTPException(
                    status_code=404,
                    detail=f"No predictions found for {crop.value} in {year}"
                )
            
            predictions = {}
            for file in files:
                # Extract day from filename using regex
                if match := re.search(rf"result{year}_(\d+)\.csv$", file.name):
                    day = match.group(1)
                    df = pd.read_csv(file)
                    prediction = df[df['FIPS'] == int(fips)]
                    
                    if not prediction.empty:
                        predictions[day] = {
                            "prediction": float(prediction.iloc[0]['y_test_pred']),
                            "actual": float(prediction.iloc[0]['y_test']),
                            "uncertainty": float(prediction.iloc[0]['y_test_pred_uncertainty'])
                        }
            
            if not predictions:
                raise HTTPException(
                    status_code=404,
                    detail=f"No predictions found for FIPS {fips}"
                )
            
            return {
                "crop": crop.value,
                "year": year,
                "fips": fips,
                "predictions": predictions
            }
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid FIPS code")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 