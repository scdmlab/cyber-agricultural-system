from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
import os

from routers import model, prediction

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the model router
app.include_router(model.router)

# Include the prediction router
app.include_router(prediction.router)

# Data directory configuration
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RESULT_DIR = BASE_DIR / "result_corn"
RESULT_SOYBEAN_DIR = BASE_DIR / "result_soybean"

@app.get("/api/data/{crop}/{year}/{month}.json")
async def get_map_data(crop: str, year: str, month: str):
    try:
        file_path = DATA_DIR / crop / year / f"{month}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Data not found: {file_path}")
        return file_path.read_text()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/corn_yield_US.csv")
async def get_historical_data():
    try:
        file_path = DATA_DIR / "corn_yield_US.csv"
        df = pd.read_csv(file_path)
        df = df.replace([float('inf'), float('-inf')], None)
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/average_pred.csv")
async def get_average_pred():
    try:
        file_path = DATA_DIR / "average_pred.csv"
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/county.csv")
async def get_county_data():
    try:
        file_path = DATA_DIR / "county.csv"
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/county_info.csv")
async def get_county_info():
    try:
        file_path = DATA_DIR / "county_info.csv"
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predictions/{crop}/{year}")
async def get_predictions(crop: str, year: str):
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