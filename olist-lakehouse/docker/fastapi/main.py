from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow.pyfunc
import pandas as pd
import numpy as np
import os

app = FastAPI(title="Olist Price Predictor API")

# Use the actual run_id from training
RUN_ID = "a50d24cfab964915bd975dfdad7fc551"
MODEL = None

class PredictionInput(BaseModel):
    freight_value: float
    delivery_days: float
    review_score: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "freight_value": 15.5,
                "delivery_days": 7.0,
                "review_score": 4.2
            }
        }

class PredictionOutput(BaseModel):
    predicted_price: float
    input_features: dict

@app.on_event("startup")
async def load_model():
    """Load model on startup"""
    global MODEL
    try:
        # Set MLflow tracking URI
        mlflow.set_tracking_uri("file:///app/mlruns")
        
        # Load model using run_id
        model_uri = f"runs:/{RUN_ID}/model"
        MODEL = mlflow.pyfunc.load_model(model_uri)
        print(f"✅ Model loaded successfully from run: {RUN_ID}")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise e

@app.post("/predict", response_model=PredictionOutput)
async def predict(input_data: PredictionInput):
    """Make price prediction"""
    try:
        if MODEL is None:
            raise HTTPException(status_code=500, detail="Model not loaded")
        
        # Prepare input data matching training schema exactly
        input_df = pd.DataFrame({
            'freight_value': [float(input_data.freight_value)],
            'delivery_days': [float(input_data.delivery_days)],
            'review_score': [str(input_data.review_score)]  # Convert to string as expected by model
        })
        
        # Convert columns to match training data types
        input_df['freight_value'] = input_df['freight_value'].astype('float64')
        input_df['delivery_days'] = input_df['delivery_days'].astype('float64')
        input_df['review_score'] = input_df['review_score'].astype('str')
        
        print(f"📊 Input DataFrame:\n{input_df}")
        print(f"📊 DataFrame dtypes:\n{input_df.dtypes}")
        
        # Make prediction
        prediction = MODEL.predict(input_df)
        predicted_price = float(prediction[0])
        
        print(f"🎯 Prediction: {predicted_price}")
        
        return PredictionOutput(
            predicted_price=round(predicted_price, 2),
            input_features={
                "freight_value": input_data.freight_value,
                "delivery_days": input_data.delivery_days,
                "review_score": input_data.review_score
            }
        )
        
    except Exception as e:
        print(f"❌ Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_status = "loaded" if MODEL is not None else "not_loaded"
    return {
        "status": "healthy",
        "model_status": model_status,
        "run_id": RUN_ID
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Olist Price Predictor API",
        "docs": "/docs",
        "health": "/health"
    }
