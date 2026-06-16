import streamlit as st

from scripts.data_provider import load_matches
from components.auth_manager import render_authentication
from components.tabs_manager import render_tabs

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="World Cup 2026 Predictions",
    layout="wide"
)

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

DB_URL = "YOUR_DATABASE_URL"

try:
    conn = st.connection(
        "supabase",
        type="sql",
        url=DB_URL
    )
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
# LOAD DATA
# --------------------------------------------------

matches_df = load_matches()

# --------------------------------------------------
# APP
# --------------------------------------------------

st.title("World Cup 2026 Predictions Tournament")

if not st.session_state.logged_in:

    render_authentication(conn)

else:

    st.sidebar.write(
        f"Welcome, {st.session_state.username}"
    )

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    st.info(
        "Note: All match times and dates are displayed in Egypt Standard Time."
    )

    render_tabs(conn, matches_df)
