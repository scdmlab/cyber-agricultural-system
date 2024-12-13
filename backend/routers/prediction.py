from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import pandas as pd
from enum import Enum
import re

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
VALID_CROPS = ["corn", "soybean"]

# Define enums for validation
class CropType(str, Enum):
    corn = "corn"
    soybean = "soybean"

class PredictionType(str, Enum):
    end_of_season = "end_of_season"
    in_season = "in_season"

def get_all_prediction_files(crop: str, year: str) -> list[Path]:
    """Helper function to get all prediction files for a year"""
    result_dir = BASE_DIR / f"result_{crop}" / "bnn"
    return list(result_dir.glob(f"result{year}*.csv"))

@router.get("/api/predictions/{crop}/{year}/{prediction_type}/{fips}",
    summary="Get Crop Yield Predictions",
    description="""
    Retrieves crop yield predictions for a specific county (FIPS code).
    
    Parameters:
    - crop: Type of crop (corn or soybean)
    - year: Prediction year
    - prediction_type: Either 'end_of_season' or 'in_season'
    - fips: County FIPS code
    
    Returns predictions and uncertainty estimates.
    """)
async def get_predictions(
    crop: CropType,
    year: str,
    prediction_type: PredictionType,
    fips: str
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