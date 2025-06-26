import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import os
import boto3
import random
import io
# from PIL import Image # Opsional, jika ingin resize dengan Pillow

st.set_page_config(
    page_title="Olist Price Predictor",
    page_icon="🛒",
    layout="wide"
)

# --- MinIO Configuration & Helper ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_RAW_BUCKET_NAME = os.getenv("MINIO_RAW_BUCKET_NAME", "raw")
IMAGE_BASE_PATH_IN_BUCKET = "images/"

@st.cache_resource
def get_s3_client():
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY
        )
        s3.list_buckets()
        return s3
    except Exception as e:
        print(f"Error connecting to MinIO: {e}")
        return None

s3_client = get_s3_client()

@st.cache_data(ttl=3600)
def get_all_image_keys_from_minio(_s3_client_placeholder):
    if not s3_client:
        return [], "S3 client not initialized."
    all_image_keys = []
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=MINIO_RAW_BUCKET_NAME, Prefix=IMAGE_BASE_PATH_IN_BUCKET)
        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    key = obj["Key"]
                    if not key.endswith('/') and key.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        all_image_keys.append(key)
        if not all_image_keys:
            return [], "No images found in MinIO under the specified path."
        return all_image_keys, None
    except Exception as e:
        return [], f"Error listing images: {str(e)}"

def get_random_images_data(image_keys_list, num_images=3):
    if not s3_client or not image_keys_list:
        return []
    selected_images_data = []
    if not image_keys_list:
        return selected_images_data
    num_to_select = min(num_images, len(image_keys_list))
    if num_to_select == 0:
        return selected_images_data
    random_image_keys = random.sample(image_keys_list, num_to_select)
    for key in random_image_keys:
        try:
            response = s3_client.get_object(Bucket=MINIO_RAW_BUCKET_NAME, Key=key)
            image_data = response['Body'].read()
            selected_images_data.append({"data": image_data, "key": key})
        except Exception as e:
            print(f"Error fetching image data for {key}: {e}")
    return selected_images_data

# --- End of MinIO Helper ---


# --- Display Random Ad Images ---
IMAGE_DISPLAY_WIDTH = 200 # Tentukan lebar yang diinginkan di sini

if s3_client:
    st.sidebar.caption(f"✔️ MinIO Client Connected")
    all_img_keys, error_listing_keys = get_all_image_keys_from_minio(str(s3_client))
    if error_listing_keys:
        st.warning(f"Could not list ad images: {error_listing_keys}")
    elif not all_img_keys:
        st.info("No ad images found to display.")
    else:
        random_images = get_random_images_data(all_img_keys, num_images=3)
        if random_images:
            st.subheader("✨ Featured Products / Inspirations ✨")
            cols = st.columns(len(random_images))
            for i, img_info in enumerate(random_images):
                with cols[i]:
                    # Menggunakan argumen width
                    st.image(
                        img_info["data"], 
                        width=IMAGE_DISPLAY_WIDTH, # Atur lebar gambar
                        caption=f"{img_info['key'].split('/')[-2]}/{img_info['key'].split('/')[-1]}"
                    )
            st.markdown("---")
        elif not error_listing_keys:
             st.info("Could not retrieve random images at the moment.")
else:
    st.sidebar.error(f"⚠️ MinIO Client Connection Failed. Ads disabled.")
# --- End of Display Random Ad Images ---


st.title("🛒 Olist E-commerce Price Predictor")
st.markdown("### Predict product prices based on cost, freight, delivery time, and customer reviews")

# Sidebar for API info
st.sidebar.header("⚙️ System Status")
try:
    health_response = requests.get("http://fastapi:8000/health") 
    if health_response.status_code == 200:
        health_data = health_response.json()
        st.sidebar.success("✅ API Connected")
        st.sidebar.info(f"**Run ID:** `{health_data.get('run_id', 'N/A')[:8]}...`")
        st.sidebar.info(f"**Model Status:** `{health_data.get('model_status', 'Unknown').capitalize()}`")
    else:
        st.sidebar.error(f"❌ API Disconnected (Status: {health_response.status_code})")
except requests.exceptions.ConnectionError:
    st.sidebar.error("❌ API Connection Error\n(Is FastAPI service running?)")
except Exception as e:
    st.sidebar.error(f"❌ API Unavailable: {str(e)[:50]}...")

# Main prediction interface
input_col, summary_col = st.columns([2, 1])

with input_col:
    st.header("📝 Input Product Details")
    
    with st.form("prediction_form"):
        cost_price = st.number_input(
            "Cost Price (R$)",
            min_value=0.01,
            value=50.0,
            step=0.01,
            format="%.2f",
            help="Your cost for the product (harga modal)."
        )

        freight_value = st.number_input(
            "Freight Value (R$)", 
            min_value=0.0, 
            max_value=200.0,
            value=15.5, 
            step=0.5,
            format="%.2f",
            help="Shipping cost to the customer in Brazilian Reais."
        )
        
        delivery_days = st.number_input(
            "Delivery Days", 
            min_value=0, 
            max_value=60,
            value=7, 
            step=1,
            help="Expected delivery time to customer in days."
        )
        
        review_score = st.number_input(
            "Expected Review Score", 
            min_value=1.0, 
            max_value=5.0,
            value=4.2, 
            step=0.1,
            format="%.1f",
            help="Anticipated customer satisfaction score (1-5)."
        )
        
        submit_button = st.form_submit_button("🔮 Predict Selling Price", use_container_width=True)

with summary_col:
    st.header("📊 Input Summary")
    
    st.metric("Cost Price", f"R$ {cost_price:.2f}")
    st.metric("Freight Cost", f"R$ {freight_value:.2f}")
    st.metric("Delivery Time", f"{int(delivery_days)} days")
    st.metric("Review Score", f"{review_score:.1f}/5 ⭐")
    
    st.markdown("---") 
    st.subheader("Quick Assessment:")
    if delivery_days <= 5:
        st.success("🚀 Fast Delivery Potential")
    elif delivery_days <= 10:
        st.warning("📦 Standard Delivery Time")
    else:
        st.error("🐌 Slow Delivery Expected")
        
    if review_score >= 4.5:
        st.success("🌟 Excellent Review Potential")
    elif review_score >= 3.5:
        st.warning("👍 Good Review Potential")
    else:
        st.error("👎 Risk of Low Reviews")

if submit_button:
    st.markdown("---")
    st.header("📈 Prediction Results")
    with st.spinner("🤖 Contacting model for prediction..."):
        try:
            payload = {
                "cost_price": float(cost_price),
                "freight_value": float(freight_value),
                "delivery_days": float(delivery_days),
                "review_score": float(review_score) 
            }
            response = requests.post("http://fastapi:8000/predict", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                predicted_price = result["predicted_price"]
                
                st.success("🎯 Prediction Complete!")
                
                res_col1, res_col2, res_col3 = st.columns(3)
                
                with res_col1:
                    st.metric(
                        "💰 Predicted Selling Price", 
                        f"R$ {predicted_price:.2f}",
                        help="The price your product might sell for, predicted by the model."
                    )
                
                with res_col2:
                    profit_value = predicted_price - cost_price - freight_value
                    profit_percentage = (profit_value / predicted_price) * 100 if predicted_price > 0 else 0
                    
                    st.metric(
                        "💸 Estimated Gross Profit", 
                        f"R$ {profit_value:.2f}",
                        delta=f"{profit_percentage:.1f}% of Selling Price" if predicted_price > 0 else None,
                        delta_color="normal" if profit_value == 0 else ("inverse" if profit_value < 0 else "normal"),
                        help="Predicted Selling Price - Cost Price - Freight Value."
                    )
                
                with res_col3:
                    price_per_day = predicted_price / max(float(delivery_days), 1.0) 
                    st.metric(
                        "⚙️ Price/Delivery Day Ratio", 
                        f"R$ {price_per_day:.2f}",
                        help="A ratio indicating predicted price value per day of delivery wait time."
                    )
                
                st.markdown("---")
                st.subheader("📊 Input Feature Analysis (Visual Comparison)")
                
                max_viz_cost_price = 500.0  
                max_viz_freight = 200.0     
                max_viz_delivery = 60.0     
                max_viz_review = 5.0        

                feature_data = pd.DataFrame({
                    'Feature': ['Cost Price', 'Freight Value', 'Delivery Days', 'Review Score'],
                    'Original Value': [cost_price, freight_value, delivery_days, review_score],
                    'Normalized Value': [
                        min(float(cost_price) / max_viz_cost_price, 1.0), 
                        min(float(freight_value) / max_viz_freight, 1.0),
                        min(float(delivery_days) / max_viz_delivery, 1.0),
                        min(float(review_score) / max_viz_review, 1.0)
                    ]
                })
                feature_data['Normalized Value'] = feature_data['Normalized Value'].clip(lower=0)

                fig = px.bar(
                    feature_data, 
                    x='Feature', 
                    y='Normalized Value',
                    title="Input Features (Scaled to 0-1 for Visual Comparison)",
                    color='Feature', 
                    labels={'Normalized Value': 'Scaled Value (0-1)'},
                    text='Original Value', 
                    height=400
                )
                fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig.update_yaxes(range=[0, 1.1]) 
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.error(f"❌ API Error (HTTP {response.status_code})")
                try:
                    error_detail = response.json()
                    st.json(error_detail) 
                except : 
                    st.text(f"Raw error content:\n{response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Prediction API Connection Error. Please ensure the FastAPI service is running and accessible.")
        except Exception as e:
            st.error(f"❌ An unexpected error occurred during prediction: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

st.markdown("---")
st.header("ℹ️ About This Application & Model")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.info("""
    **🤖 Model Details:**
    - Algorithm: Random Forest Regressor
    - Features: 4 (cost_price, freight_value, delivery_days, review_score)
    - Training Data: ~107K Olist orders
    - Performance: ~54 R$ MAE
    """)

with info_col2:
    st.info("""
    **📈 Potential Use Cases:**
    - Price optimization for sellers
    - Market analysis
    - Revenue forecasting
    - Competitive pricing strategy
    """)

st.markdown("<div style='text-align: center;'>Powered by Streamlit, FastAPI, MLflow, and Spark</div>", unsafe_allow_html=True)