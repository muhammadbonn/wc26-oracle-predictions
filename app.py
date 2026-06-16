import streamlit as st
import pandas as pd
from scripts.data_provider import load_matches
from components.auth_manager import render_auth_logic
from components.tabs_manager import render_upcoming_tab, render_history_tab

# Page setup
st.set_page_config(page_title="World Cup 2026 Predictions", layout="wide")

# Database connection
db_url = "postgresql://postgres.pjopqzmxaapwmfootrcb:3EK.tt9z_B$9b$G@aws-0-eu-west-3.pooler.supabase.com:5432/postgres"
try:
    conn = st.connection("supabase", type="sql", url=db_url)
except Exception as e:
    st.error(f"Database connection error: {e}")

# Global data loading
matches_df = load_matches()

# State Management
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

st.title("World Cup 2026 Predictions Tournament")

# Logic Flow
if not st.session_state.logged_in:
    render_auth_logic(conn)
else:
    # Sidebar
    st.sidebar.write(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    st.info("Note: All match times and dates are displayed in Egypt Standard Time.")
    
    # 4 distinct tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Upcoming Matches", "Match History", "Leaderboard", "Tournament Rules"])

    # Prepare data for tabs
    from scripts.db_predictions import get_user_predictions, get_all_predictions
    from scripts.utils import get_match_round
    
    current_egypt_time = pd.Timestamp.now() + pd.Timedelta(hours=3)
    my_preds = get_user_predictions(conn, st.session_state.username)
    pred_dict = {str(row['match_id']): {
        'predicted_outcome': row['predicted_outcome'],
        'predict_goals': row['predict_goals'],
        'home_score': row['home_score'],
        'away_score': row['away_score']
    } for _, row in my_preds.iterrows()}

    if not matches_df.empty:
        matches_df['round_name'] = matches_df['match_id'].apply(get_match_round)
        matches_df['date_group'] = matches_df['match_time'].dt.strftime('%A - %B %d, %Y')
        
        upcoming_df = matches_df[matches_df['match_time'] > current_egypt_time].sort_values(by='match_time')
        past_df = matches_df[matches_df['match_time'] <= current_egypt_time].sort_values(by='match_time')

        with tab1:
            render_upcoming_tab(upcoming_df, pred_dict, conn, st.session_state.username)
        with tab2:
            render_history_tab(past_df, pred_dict)
        with tab3:
            # You can also move this to tabs_manager if desired
            st.header("Leaderboard Standings")
            # ... (Leaderboard logic from previous code)
        with tab4:
            st.header("Tournament Rules")
            try:
                with open("data/rules.txt", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            except:
                st.error("Rules file not found.")
