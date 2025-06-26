import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import mlflow
import mlflow.sklearn
import os
import io
import boto3

mlflow.set_tracking_uri("file:///app/mlruns")

minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")

s3_client = boto3.client(
    's3',
    endpoint_url=minio_endpoint,
    aws_access_key_id=minio_access_key,
    aws_secret_access_key=minio_secret_key,
)

gold_bucket_name = "gold"
gold_prefix = "olist_features/"

def load_data_from_minio():
    try:
        objects = s3_client.list_objects_v2(Bucket=gold_bucket_name, Prefix=gold_prefix)
        parquet_files = [obj['Key'] for obj in objects.get('Contents', []) if obj['Key'].endswith('.parquet')]
        
        if not parquet_files:
            raise FileNotFoundError(f"No parquet files found in MinIO bucket '{gold_bucket_name}' with prefix '{gold_prefix}'")
        
        all_dfs = []
        for p_file_key in parquet_files:
            print(f"Reading {p_file_key} from MinIO bucket {gold_bucket_name}...")
            response = s3_client.get_object(Bucket=gold_bucket_name, Key=p_file_key)
            file_content = response['Body'].read()
            df_part = pd.read_parquet(io.BytesIO(file_content))
            all_dfs.append(df_part)
        
        if not all_dfs:
             raise FileNotFoundError("Could not read any parquet data from MinIO.")
        
        df = pd.concat(all_dfs, ignore_index=True)

        print(f"✅ Loaded data from MinIO: s3a://{gold_bucket_name}/{gold_prefix}")
        print(f"📊 Data shape: {df.shape}")
        print(f"📊 Columns: {df.columns.tolist()}")
        return df
    except Exception as e:
        print(f"❌ Error loading data from MinIO: {e}")
        raise

def train_model():
    """Train ML model for price prediction"""
    mlflow.set_experiment("olist-price-prediction")
    
    with mlflow.start_run() as run:
        print("🚀 Starting model training...")
        
        df = load_data_from_minio()
        
        print("🔧 Preprocessing data...")
        df = df.dropna()
        if 'price' in df.columns and pd.api.types.is_numeric_dtype(df['price']):
            df = df[(df['price'] > 0) & (df['price'] < df['price'].quantile(0.99))]
        else:
            print("⚠️ Kolom 'price' tidak ada atau bukan numerik. Skipping price filtering.")

        if 'cost_price' in df.columns and pd.api.types.is_numeric_dtype(df['cost_price']):
            df = df[df['cost_price'] > 0] 
        else:
            print("⚠️ Kolom 'cost_price' tidak ada atau bukan numerik. Skipping cost_price filtering.")

        if 'freight_value' in df.columns and pd.api.types.is_numeric_dtype(df['freight_value']):
            df = df[df['freight_value'] >= 0]
        else:
            print("⚠️ Kolom 'freight_value' tidak ada atau bukan numerik. Skipping freight_value filtering.")

        if 'delivery_days' in df.columns:
            df['delivery_days'] = pd.to_numeric(df['delivery_days'], errors='coerce')
            df = df[df['delivery_days'].notna()]
            df = df[(df['delivery_days'] >= 0) & (df['delivery_days'] <= 100)]
        else:
            print("⚠️ Kolom 'delivery_days' tidak ada. Skipping delivery_days filtering.")
        
        if 'review_score' in df.columns:
             df['review_score'] = df['review_score'].astype(str)

        print(f"📊 Data after cleaning: {df.shape}")
        
        potential_features = ['cost_price', 'freight_value', 'delivery_days', 'review_score']
        available_features = [col for col in potential_features if col in df.columns]
        
        print(f"Using features: {available_features}")
        
        if len(available_features) < 2 :
            raise ValueError(f"Not enough valid features found! Found: {available_features}")
            
        X = df[available_features]
        y = df['price']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"📈 Training set: {X_train.shape}")
        print(f"📉 Test set: {X_test.shape}")
        
        print("🤖 Training Random Forest model...")
        model = RandomForestRegressor(
            n_estimators=50, max_depth=10, random_state=42, n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)
        
        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
        
        print(f"📊 Training MAE: {train_mae:.2f}")
        print(f"📊 Test MAE: {test_mae:.2f}")
        print(f"📊 Training RMSE: {train_rmse:.2f}")
        print(f"📊 Test RMSE: {test_rmse:.2f}")
        
        mlflow.log_param("n_estimators", 50)
        mlflow.log_param("max_depth", 10)
        mlflow.log_param("features", available_features)
        
        mlflow.log_metric("train_mae", train_mae)
        mlflow.log_metric("test_mae", test_mae)
        mlflow.log_metric("train_rmse", train_rmse)
        mlflow.log_metric("test_rmse", test_rmse)
        
        if not X_train.empty:
            mlflow.sklearn.log_model(
                model, 
                "model",
                input_example=X_train.head(1) 
            )
        else:
            print("⚠️ Training data is empty, cannot log model with input example.")
            mlflow.sklearn.log_model(model, "model")

        run_id = run.info.run_id
        print(f"🎯 Model saved with run_id: {run_id}")
        
        return run_id

if __name__ == "__main__":
    try:
        run_id = train_model()
        print(f"✅ Training completed successfully!")
        print(f"📝 Run ID: {run_id}")
        
        print("\n📁 MLflow artifacts (metadata & model files) are in the 'mlruns' directory.")
        
    except Exception as e:
        print(f"❌ Training failed: {str(e)}")
        import traceback
        traceback.print_exc()