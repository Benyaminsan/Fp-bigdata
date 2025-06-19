import streamlit as st
import requests
import json
import plotly.express as px
import pandas as pd

st.set_page_config(
    page_title="Olist Price Predictor",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 Olist E-commerce Price Predictor")
st.markdown("### Predict product prices based on freight, delivery time, and customer reviews")

# Sidebar for API info
st.sidebar.header("ℹ️ Model Info")
try:
    health_response = requests.get("http://fastapi:8000/health")
    if health_response.status_code == 200:
        health_data = health_response.json()
        st.sidebar.success("✅ API Connected")
        st.sidebar.info(f"**Run ID:** {health_data.get('run_id', 'N/A')[:8]}...")
        st.sidebar.info(f"**Model:** {health_data.get('model_status', 'Unknown')}")
    else:
        st.sidebar.error("❌ API Disconnected")
except:
    st.sidebar.error("❌ API Unavailable")

# Main prediction interface
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 Input Product Details")
    
    with st.form("prediction_form"):
        # Input controls
        freight_value = st.number_input(
            "Freight Value (R$)", 
            min_value=0.0, 
            max_value=200.0,
            value=15.5, 
            step=0.5,
            help="Shipping cost in Brazilian Reais"
        )
        
        delivery_days = st.number_input(
            "Delivery Days", 
            min_value=0, 
            max_value=60,
            value=7, 
            step=1,
            help="Expected delivery time in days"
        )
        
        review_score = st.number_input(
            "Expected Review Score", 
            min_value=1.0, 
            max_value=5.0,
            value=4.2, 
            step=0.1,
            help="Customer satisfaction score (1-5)"
        )
        
        submit_button = st.form_submit_button("🔮 Predict Price", use_container_width=True)

with col2:
    st.header("📊 Input Summary")
    
    # Display current inputs
    st.metric("Freight Cost", f"R$ {freight_value:.2f}")
    st.metric("Delivery Time", f"{delivery_days} days")
    st.metric("Review Score", f"{review_score:.1f}/5")
    
    # Quality indicators
    if delivery_days <= 5:
        st.success("🚀 Fast Delivery")
    elif delivery_days <= 10:
        st.warning("📦 Standard Delivery")
    else:
        st.error("🐌 Slow Delivery")
        
    if review_score >= 4.0:
        st.success("⭐ High Quality")
    elif review_score >= 3.0:
        st.warning("👍 Good Quality")
    else:
        st.error("👎 Low Quality")

# Prediction results
if submit_button:
    with st.spinner("🤖 Making prediction..."):
        try:
            # Call FastAPI
            response = requests.post(
                "http://fastapi:8000/predict",
                json={
                    "freight_value": freight_value,
                    "delivery_days": delivery_days,
                    "review_score": review_score
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                predicted_price = result["predicted_price"]
                
                # Display prediction result
                st.success("🎯 Prediction Complete!")
                
                # Main result
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "💰 Predicted Price", 
                        f"R$ {predicted_price:.2f}",
                        help="Machine learning prediction"
                    )
                
                with col2:
                    profit_margin = predicted_price - freight_value
                    st.metric(
                        "💵 Profit Margin", 
                        f"R$ {profit_margin:.2f}",
                        delta=f"{(profit_margin/predicted_price)*100:.1f}%"
                    )
                
                with col3:
                    price_per_day = predicted_price / max(delivery_days, 1)
                    st.metric(
                        "📈 Price/Day Ratio", 
                        f"R$ {price_per_day:.2f}",
                        help="Price efficiency per delivery day"
                    )
                
                # Feature importance visualization
                st.header("📊 Input Analysis")
                
                feature_data = pd.DataFrame({
                    'Feature': ['Freight Value', 'Delivery Days', 'Review Score'],
                    'Value': [freight_value, delivery_days, review_score],
                    'Normalized': [
                        freight_value / 100,  # Normalize to 0-1 scale
                        delivery_days / 30,
                        review_score / 5
                    ]
                })
                
                fig = px.bar(
                    feature_data, 
                    x='Feature', 
                    y='Normalized',
                    title="Feature Values (Normalized)",
                    color='Normalized',
                    color_continuous_scale='viridis'
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.text(response.text)
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to prediction API. Please check if FastAPI service is running.")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")

# Information section
st.header("ℹ️ About This Model")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    **🤖 Model Details:**
    - Algorithm: Random Forest Regressor
    - Features: 3 (freight_value, delivery_days, review_score)
    - Training Data: ~107K Olist orders
    - Performance: ~54 R$ MAE
    """)

with col2:
    st.info("""
    **📈 Use Cases:**
    - Price optimization for sellers
    - Market analysis
    - Revenue forecasting
    - Competitive pricing strategy
    """)
