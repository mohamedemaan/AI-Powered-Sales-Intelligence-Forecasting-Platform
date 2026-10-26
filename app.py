# =========================
# IMPORT LIBRARIES
# =========================

import streamlit as st  # type: ignore
import pickle
import pandas as pd  # type: ignore
import matplotlib.pyplot as plt  # type: ignore


# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Sales Prediction Dashboard",
    layout="wide"
)


# =========================
# LOAD MODEL
# =========================

try:
    with open("sales_model.pkl", "rb") as f:
        model = pickle.load(f)
except FileNotFoundError:
    model = None


# =========================
# TITLE
# =========================

st.title("🔥 Sales Prediction Dashboard")


# =========================
# SIDEBAR
# =========================

st.sidebar.header("Enter Input Values")


feature1 = st.sidebar.number_input(
    "Feature 1",
    value=0.0
)

feature2 = st.sidebar.number_input(
    "Feature 2",
    value=0.0
)

feature3 = st.sidebar.number_input(
    "Feature 3",
    value=0.0
)


# =========================
# PREDICTION
# =========================

if st.sidebar.button("Predict Sales"):
    if model is None:
        st.error("Model file 'sales_model.pkl' not found. Please train and save the model first.")
    else:
        # Provide generic column names to prevent Feature warnings in some versions of sklearn
        input_data = pd.DataFrame(
            [[feature1, feature2, feature3]],
            columns=["feature1", "feature2", "feature3"]
        )

        prediction = model.predict(input_data)

        st.success(
            f"🔥 Predicted Sales: {prediction[0]}"
        )


# =========================
# SAMPLE CHART
# =========================

st.subheader("📊 Sample Sales Chart")

sample_data = pd.DataFrame({
    "Month": ["Jan", "Feb", "Mar", "Apr", "May"],
    "Sales": [100, 150, 120, 180, 210]
})

fig, ax = plt.subplots()

ax.plot(
    sample_data["Month"],
    sample_data["Sales"]
)

ax.set_xlabel("Month")

ax.set_ylabel("Sales")

ax.set_title("Monthly Sales")

st.pyplot(fig)


# =========================
# METRICS
# =========================

col1, col2, col3 = st.columns(3)

col1.metric("Total Sales", "₹50K")

col2.metric("Growth", "12%")

col3.metric("Customers", "1,250")


# =========================
# GEMINI PRO ADVISOR
# =========================

st.subheader("💡 Ask Gemini Pro Sales Advisor")
gemini_query = st.text_input(
    "Ask Gemini about sales trends, predictions, or inventory advice:",
    placeholder="e.g. How can we increase Q3 conversion rates?"
)

if st.button("Consult Gemini"):
    if not gemini_query.strip():
        st.warning("Please enter a question first.")
    else:
        import os
        from pathlib import Path
        try:
            from dotenv import load_dotenv
            load_dotenv()
            load_dotenv(Path(__file__).parent / "backend" / ".env")
        except Exception:
            pass
        
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key or "your_" in api_key.lower():
            st.error("⚠️ GEMINI_API_KEY is not set. Please add GEMINI_API_KEY to your .env file.")
        else:
            try:
                import httpx  # type: ignore
                model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                prompt_text = f"You are a sales prediction and retail business expert. The user asks: {gemini_query}. Provide a concise, actionable business response."
                
                with st.spinner("Consulting Gemini Pro..."):
                    resp = httpx.post(
                        url,
                        json={"contents": [{"parts": [{"text": prompt_text}]}]},
                        headers={"Content-Type": "application/json"},
                        timeout=30.0
                    )
                    if resp.status_code == 200:
                        ans = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                        st.info(ans)
                    else:
                        st.error(f"Gemini API returned error: {resp.text}")
            except Exception as e:
                st.error(f"Error querying Gemini API: {e}")

# =========================
# FOOTER
# =========================

st.write("✅ AI Dashboard Created Using Streamlit & Gemini Pro")