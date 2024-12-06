from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import os
import json
import tempfile
import uuid
import numpy as np

from utils.geo_utils import validate_geojson
from utils.get_feature import get_features
from utils.run_model import run_model

router = APIRouter()

class GeoJSONRequest(BaseModel):
    type: str
    features: list[Dict[str, Any]]


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

@router.post("/api/model/",
    summary="Process GeoJSON and Get Predictions",
    description="""
    Processes GeoJSON data to extract features and generate crop yield predictions.
    
    The endpoint accepts GeoJSON data representing a field boundary and returns:
    - Predicted crop yield
    - Model uncertainty estimates
    """,
    response_description="Prediction results including yield estimate and uncertainty")
async def process_geojson(geojson_data: GeoJSONRequest):
    """
    Process GeoJSON data and return feature vector
    """
    try:
        # Validate GeoJSON
        if not validate_geojson(geojson_data.dict()):
            raise HTTPException(
                status_code=400,
                detail="Invalid GeoJSON format"
            )

        # Create temporary directory if it doesn't exist
        temp_dir = os.path.join(tempfile.gettempdir(), 'crop_prediction')
        os.makedirs(temp_dir, exist_ok=True)

        # Generate unique filename using UUID
        temp_file = os.path.join(temp_dir, f"request_{uuid.uuid4()}.json")

        # Save GeoJSON to temporary file
        with open(temp_file, 'w') as f:
            json.dump(geojson_data.dict(), f)

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
        os.remove(temp_file)

        return {
            "status": "success",
            # "features": features_dict,
            "prediction": prediction.tolist()  # Convert numpy values to Python native types
        }

    except Exception as e:
        # Log the error (implement proper logging)
        print(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        ) 