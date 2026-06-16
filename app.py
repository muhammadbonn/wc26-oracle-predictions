import streamlit as st
import pandas as pd
from scripts.data_provider import load_matches
from scripts.utils import get_team_flag, calculate_score, get_match_round
from scripts.db_users import check_user, create_user
from scripts.db_predictions import get_user_predictions, save_user_prediction, get_all_predictions

# Page setup
st.set_page_config(page_title="World Cup 2026 Predictions", layout="wide")

# Database connection
db_url = "postgresql://postgres.pjopqzmxaapwmfootrcb:3EK.tt9z_B$9b$G@aws-0-eu-west-3.pooler.supabase.com:5432/postgres"
try:
    conn = st.connection("supabase", type="sql", url=db_url)
except Exception as e:
    st.error(f"Database connection error: {e}")

matches_df = load_matches()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

st.title("World Cup 2026 Predictions Tournament")

if not st.session_state.logged_in:
    st.subheader("Authentication")
    auth_mode = st.radio("Choose Action:", ["Login", "Sign Up (New Account)"], horizontal=True)
    username = st.
