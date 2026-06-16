import streamlit as st
import pandas as pd

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="World Cup 2026 Predictions",
    layout="wide"
)

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

try:
    conn = st.connection(
        "supabase",
        type="sql"
    )

    # اختبار الاتصال
    conn.query("SELECT 1", ttl=0)

except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# --------------------------------------------------
# APP
# --------------------------------------------------

st.title("World Cup 2026 Predictions Tournament")

st.success("Database connected successfully ✅")
