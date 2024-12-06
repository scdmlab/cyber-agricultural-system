from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import os
import json
import tempfile
import uuid

from utils.geo_utils import validate_geojson
from utils.get_feature import get_features

router = APIRouter()

class GeoJSONRequest(BaseModel):
    type: str
    features: list[Dict[str, Any]]

@router.post("/api/model/")
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
        
        if features_df is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to extract features"
            )

        # Convert DataFrame to dictionary
        features_dict = features_df.to_dict(orient='records')[0]

        # Clean up temporary file
        os.remove(temp_file)

        return {
            "status": "success",
            "features": features_dict
        }

    except Exception as e:
        # Log the error (implement proper logging)
        print(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        ) 