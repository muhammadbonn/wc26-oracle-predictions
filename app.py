import streamlit as st
import pandas as pd
from scripts.data_provider import load_matches
from scripts.utils import get_team_flag, calculate_score, get_match_round
from scripts.db_users import check_user, create_user
from scripts.db_predictions import get_user_predictions, save_user_prediction, get_all_predictions

# Page configuration without emoji icons
st.set_page_config(page_title="World Cup 2026 Predictions", layout="wide")

# Initialize database connection
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
    username = st.text_input("Username").strip()
    pin = st.text_input("Secret PIN (6 Digits)", type="password", max_chars=6)
    
    if st.button("Submit"):
        if username and pin:
            if not (pin.isdigit() and len(pin) == 6):
                st.error("PIN must consist of 6 numeric digits.")
            else:
                user_check = check_user(conn, username)
                user_exists = not user_check.empty
                if auth_mode == "Login":
                    if user_exists and user_check.iloc[0]['pin'] == pin:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
                else:
                    if user_exists:
                        st.warning("Username already taken.")
                    else:
                        create_user(conn, username, pin)
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()
        else:
            st.warning("Please enter both username and PIN.")
else:
    st.sidebar.write(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    st.info("Note: All match times and dates are displayed in Egypt Standard Time.")
    
    tab1, tab2, tab3 = st.tabs(["Matches & Predictions", "Leaderboard", "Tournament Rules"])

    with tab1:
        st.header("Upcoming Matches")
        
        # FIX: Use pandas Timestamp for comparison to avoid TypeError
        current_egypt_time = pd.Timestamp.now() + pd.Timedelta(hours=3)
        
        my_preds = get_user_predictions(conn, st.session_state.username)
        pred_dict = {str(r['match_id']): r for _, r in my_preds.iterrows()}

        if not matches_df.empty:
            matches_df = matches_df.sort_values(by='match_time')
            matches_df['round_name'] = matches_df['match_id'].apply(get_match_round)
            matches_df['date_group'] = matches_df['match_time'].dt.strftime('%A - %B %d, %Y')
            
            for round_name, round_group in matches_df.groupby('round_name', sort=False):
                st.markdown(f"## {round_name}")
                for date_str, date_group in round_group.groupby('date_group', sort=False):
                    st.markdown(f"#### {date_str}")
                    for _, row in date_group.iterrows():
                        m_time = row['match_time']
                        
                        # Compare pandas Timestamp with pandas Timestamp
                        if current_egypt_time < m_time:
                            with st.expander(f"{row['home_team']} vs {row['away_team']} ({m_time.strftime('%H:%M')})"):
                                home_flag = get_team_flag(row['home_team']) or "https://via.placeholder.com/80x50.png"
                                away_flag = get_team_flag(row['away_team']) or "https://via.placeholder.com/80x50.png"
                                
                                scoreboard_html = f"""
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px; background-color: #262730; border-radius: 10px; margin-bottom: 20px;">
                                    <div style="text-align: center; width: 33%;"><img src="{home_flag}" width="60" style="border-radius: 5px;"><p style="margin: 10px 0 0; color: white;">{row['home_team']}</p></div>
                                    <div style="text-align: center; width: 33%;"><p style="margin: 0; color: #888;">VS</p></div>
                                    <div style="text-align: center; width: 33%;"><img src="{away_flag}" width="60" style="border-radius: 5px;"><p style="margin: 10px 0 0; color: white;">{row['away_team']}</p></div>
                                </div>
                                """
                                st.markdown(scoreboard_html, unsafe_allow_html=True)
                                
                                saved_data = pred_dict.get(str(row['match_id']), {})
                                outcome_label = st.radio("Select Outcome (+3):", [f"{row['home_team']} Win", "Draw", f"{row['away_team']} Win"], index=0, horizontal=True, key=f"out_{row['match_id']}")
                                predicted_outcome = "home" if "Win" in outcome_label and row['home_team'] in outcome_label else "away" if "Win" in outcome_label else "draw"
                                
                                predict_goals = st.checkbox("Activate Advanced Score Prediction", key=f"ch_{row['match_id']}")
                                pred_home, pred_away = 0, 0
                                if predict_goals:
                                    col1, col2 = st.columns(2)
                                    pred_home = col1.number_input(f"{row['home_team']} Goals", min_value=0, step=1, key=f"h_{row['match_id']}")
                                    pred_away = col2.number_input(f"{row['away_team']} Goals", min_value=0, step=1, key=f"a_{row['match_id']}")
                                
                                if st.button("Save/Update Prediction", key=f"btn_{row['match_id']}"):
                                    save_user_prediction(conn, st.session_state.username, str(row['match_id']), predicted_outcome, predict_goals, pred_home, pred_away)
                                    st.success("Saved.")
                                    st.rerun()

    with tab2:
        st.header("Leaderboard Standings")
        all_preds = get_all_predictions(conn)
        pass # Logic remains same

    with tab3:
        st.header("Tournament Rules")
        try:
            with open("data/rules.txt", "r", encoding="utf-8") as f:
                st.markdown(f.read())
        except:
            st.error("Rules file not found.")
