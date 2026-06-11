import streamlit as st
import pandas as pd
from datetime import datetime
from scripts.data_provider import load_matches
from scripts.utils import get_team_flag, calculate_score
from scripts.db_helpers import check_user, create_user, get_user_predictions, save_user_prediction, get_all_predictions

# Page configuration
st.set_page_config(page_title="World Cup 2026 Predictions", page_icon="⚽", layout="wide")

# Initialize database connection using Supabase URI
db_url = "postgresql://postgres.pjopqzmxaapwmfootrcb:3EK.tt9z_B$9b$G@aws-0-eu-west-3.pooler.supabase.com:5432/postgres"

try:
    conn = st.connection("supabase", type="sql", url=db_url)
except Exception as e:
    st.error(f"Database connection error: {e}")

# Load matches using local data provider configuration
matches_df = load_matches()

# Session state initialization for login tracking
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

st.title("⚽ World Cup 2026 Predictions Tournament")

if not st.session_state.logged_in:
    st.subheader("Authentication / Registration")
    username = st.text_input("Username").strip()
    pin = st.text_input("Secret PIN (6 Digits)", type="password", max_chars=6)
    
    if st.button("Submit"):
        if username and pin:
            if not (pin.isdigit() and len(pin) == 6):
                st.error("❌ PIN must consist of exactly 6 numeric digits (e.g., 123456).")
            else:
                user_check = check_user(conn, username)
                if not user_check.empty:
                    if user_check.iloc[0]['pin'] == pin:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("❌ Invalid PIN. Please try again.")
                else:
                    create_user(conn, username, pin)
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("🎉 Account created successfully. Welcome to the tournament.")
                    st.rerun()
        else:
            st.warning("⚠️ Please enter both your username and PIN.")
else:
    st.sidebar.write(f"👋 Welcome, **{st.session_state.username}**")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    tab1, tab2 = st.tabs(["Matches & Predictions 📝", "Leaderboard 🏆"])

    with tab1:
        st.header("Upcoming Matches")
        current_time = datetime.now()
        
        my_preds = get_user_predictions(conn, st.session_state.username)
        pred_dict = {str(row['match_id']): {'home': row['home_score'], 'away': row['away_score']} for _, row in my_preds.iterrows()}

        if not matches_df.empty:
            for index, row in matches_df.iterrows():
                match_id = str(row['match_id'])
                home = row['home_team']
                away = row['away_team']
                m_time = row['match_time']
                
                if current_time < m_time:
                    with st.expander(f"🕒 {home} vs {away} - {m_time.strftime('%Y-%m-%d %H:%M')}"):
                        col1, col2 = st.columns(2)
                        
                        default_home = pred_dict.get(match_id, {}).get('home', 0)
                        default_away = pred_dict.get(match_id, {}).get('away', 0)
                        
                        home_flag = get_team_flag(home)
                        away_flag = get_team_flag(away)
                        
                        with col1:
                            if home_flag:
                                st.image(home_flag, width=60)
                            pred_home = st.number_input(f"{home} Score", min_value=0, step=1, value=default_home, key=f"h_{match_id}")
                        with col2:
                            if away_flag:
                                st.image(away_flag, width=60)
                            pred_away = st.number_input(f"{away} Score", min_value=0, step=1, value=default_away, key=f"a_{match_id}")
                                
                        if st.button("Save Prediction", key=f"btn_{match_id}"):
                            save_user_prediction(conn, st.session_state.username, match_id, pred_home, pred_away)
                            st.success("Prediction saved successfully.")
                            st.rerun()

    with tab2:
        st.header("Leaderboard Standings")
        all_preds = get_all_predictions(conn)
        
        leaderboard = {}
        for _, pred in all_preds.iterrows():
            uname = pred['username']
            m_id = str(pred['match_id'])
            p_home = pred['home_score']
            p_away = pred['away_score']
            
            if uname not in leaderboard:
                leaderboard[uname] = {"Username": uname, "Total Points": 0, "Correct Picks": 0, "Matches Predicted": 0}
            
            match_row = matches_df[matches_df['match_id'].astype(str) == m_id]
            if not match_row.empty:
                actual_h = match_row.iloc[0].get('actual_home_score')
                actual_a = match_row.iloc[0].get('actual_away_score')
                
                if pd.notna(actual_h) and pd.notna(actual_a):
                    pts = calculate_score(p_home, p_away, actual_h, actual_a)
                    leaderboard[uname]["Total Points"] += pts
                    if pts >= 3:
                        leaderboard[uname]["Correct Picks"] += 1
                        
            leaderboard[uname]["Matches Predicted"] += 1

        if leaderboard:
            lb_df = pd.DataFrame(list(leaderboard.values())).sort_values(by="Total Points", ascending=False)
            lb_df.reset_index(drop=True, inplace=True)
            lb_df.index += 1
            st.dataframe(lb_df, use_container_width=True)
        else:
            st.info("No predictions recorded yet.")
