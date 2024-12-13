from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from fastapi.responses import JSONResponse
import tempfile
from pathlib import Path  # Using Path from pathlib instead of os.path
import json
import uuid
import numpy as np

from utils.geo_utils import validate_geojson
from utils.get_feature import get_features
from utils.run_model import run_model

router = APIRouter(
    prefix="/api"
)

class GeoJSONGeometry(BaseModel):
    type: str = Field(..., example="Polygon")
    coordinates: List[List[List[float]]] = Field(..., description="Array of coordinates defining the polygon")

class GeoJSONProperties(BaseModel):
    GEO_ID: str = Field(..., example="0500000US55025")
    STATE: str = Field(..., example="55")
    COUNTY: str = Field(..., example="025")
    NAME: str = Field(..., example="Dane")
    LSAD: str = Field(..., example="County")
    CENSUSAREA: float = Field(..., example=1197.239)

class GeoJSONFeature(BaseModel):
    type: str = Field(..., example="Feature")
    properties: GeoJSONProperties
    geometry: GeoJSONGeometry

class GeoJSONRequest(BaseModel):
    type: str = Field(..., example="FeatureCollection")
    features: List[GeoJSONFeature]

    class Config:
        schema_extra = {
            "example": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {
                        "GEO_ID": "0500000US55025",
                        "STATE": "55",
                        "COUNTY": "025",
                        "NAME": "Dane",
                        "LSAD": "County",
                        "CENSUSAREA": 1197.239
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-89.369127, 42.845046],
                            [-89.369069, 42.856471],
                            [-89.838167, 42.857397],
                            [-89.838135, 43.206057],
                            [-89.720295, 43.292928],
                            [-89.009139, 43.28483],
                            [-89.00892, 43.197721],
                            [-89.013489, 42.847347],
                            [-89.369127, 42.845046]
                        ]]
                    }
                }]
            }
        }

class PredictionResponse(BaseModel):
    status: str = Field(..., example="success")
    prediction: List[float] = Field(..., description="Model predictions for crop yield")

import numpy as np
import pandas as pd

def rearrange_features(features_dict):
    """
    Rearrange features into the correct order for the model
    
    Args:
        features_dict (dict): Dictionary containing feature values
        
    Returns:
        numpy.ndarray: Ordered feature vector
    """
    # Define static features order
    STATIC_FEATURES = ['awc', 'cec', 'som']
    
    # Define dynamic features and their DOYs
    DYNAMIC_FEATURES = [
        'EVI', 'NDVI', 'GCI', 'NDWI', 'LSTday', 'LSTnight', 
        'ppt', 'tmax', 'tmean', 'tmin', 'tdmean', 'vpdmax', 'vpdmean', 'vpdmin',
        'Evap', 'GLDASws', 'PotEvap', 'RootMoist'
    ]
    
    DOYS = [f"{x:03d}" for x in range(58, 299, 16)]  # 058, 074, ..., 298
    
    # Create ordered feature list
    ordered_features = []
    
    # Add static features
    for feat in STATIC_FEATURES:
        ordered_features.append(features_dict.get(feat, 0))
    
    # Add dynamic features
    for feat in DYNAMIC_FEATURES:
        for doy in DOYS:
            key = f"{feat}_{doy}"
            ordered_features.append(features_dict.get(key, 0))
    
    # Convert to numpy array and ensure float32 type
    return np.array(ordered_features, dtype=np.float32)

def verify_feature_vector(feature_vector):
    """
    Verify that the feature vector has the correct length and type
    
    Args:
        feature_vector (numpy.ndarray): Feature vector to verify
        
    Returns:
        bool: True if vector is valid, False otherwise
    """
    EXPECTED_LENGTH = 291  # 3 static + 18 dynamic * 16 time steps
    
    if not isinstance(feature_vector, np.ndarray):
        print(f"Error: Expected numpy.ndarray, got {type(feature_vector)}")
        return False
    
    if feature_vector.dtype != np.float32:
        print(f"Error: Expected dtype float32, got {feature_vector.dtype}")
        return False
    
    if len(feature_vector) != EXPECTED_LENGTH:
        print(f"Error: Expected length {EXPECTED_LENGTH}, got {len(feature_vector)}")
        return False
    
    return True

@router.post("/model/",
    response_model=PredictionResponse,
    summary="Generate Crop Yield Predictions",
    description="""
    Processes field boundary GeoJSON data to predict crop yields.
    
    This endpoint:
    1. Validates the input GeoJSON format
    2. Extracts relevant features from satellite and weather data
    3. Processes features through a machine learning model
    4. Returns predicted crop yield with uncertainty estimates
    
    The prediction is based on:
    - Static soil properties (awc, cec, som)
    - Dynamic features including vegetation indices (EVI, NDVI, etc.)
    - Weather data (precipitation, temperature, etc.)
    - Satellite-derived moisture indices
    """,
    responses={
        200: {
            "description": "Successful prediction",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "prediction": [156.78]
                    }
                }
            }
        },
        400: {
            "description": "Invalid GeoJSON format",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid GeoJSON format"}
                }
            }
        },
        500: {
            "description": "Server processing error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error processing request: [error details]"}
                }
            }
        }
    }
)
async def process_geojson(geojson_data: GeoJSONRequest):
    try:
        # Validate GeoJSON
        if not validate_geojson(geojson_data.dict()):
            raise HTTPException(status_code=400, detail="Invalid GeoJSON format")

        # Create temporary directory using pathlib
        temp_dir = Path(tempfile.gettempdir()) / 'crop_prediction'
        temp_dir.mkdir(exist_ok=True)

        # Generate unique filename
        temp_file = temp_dir / f"request_{uuid.uuid4()}.json"

        # Save GeoJSON to temporary file
        temp_file.write_text(json.dumps(geojson_data.dict()))

        # Get features
        features_df = get_features(temp_file)

        # replace nan with 0
        features_df = features_df.fillna(0)
        
        if features_df is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to extract features"
            )

        # Convert DataFrame to dictionary
        features_dict = features_df.to_dict(orient='records')[0]

        # Rearrange features
        feature_vector = rearrange_features(features_dict)
        
        # Verify feature vector
        if not verify_feature_vector(feature_vector):
            raise HTTPException(
                status_code=500,
                detail="Invalid feature vector generated"
            )
        
        # Add year and padding to create 293-length vector
        final_vector = np.concatenate([[2024, 0], feature_vector])

        # random for testing
        # final_vector = np.random.rand(1, 293)
        
        # Reshape for model input (expecting shape (1, 293))
        model_input = final_vector.reshape(1, -1)
        
        # Run model prediction
        prediction = run_model(model_input)

        # Clean up temporary file
        temp_file.unlink()

        return PredictionResponse(
            status="success",
            prediction=prediction.tolist()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}") 