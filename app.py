import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
from scripts.data_provider import load_matches
from scripts.utils import get_team_flag, calculate_score, get_match_round

# Import atomic database helpers from separate modules
from scripts.db_users import check_user, create_user
from scripts.db_predictions import get_user_predictions, save_user_prediction, get_all_predictions

# Page configuration without emoji icons
st.set_page_config(page_title="World Cup 2026 Predictions", layout="wide")

# Initialize database connection using Supabase URI
db_url = "postgresql://postgres.pjopqzmxaapwmfootrcb:3EK.tt9z_B$9b$G@aws-0-eu-west-3.pooler.supabase.com:5432/postgres"

try:
    conn = st.connection("supabase", type="sql", url=db_url)
except Exception as e:
    st.error(f"Database connection error: {e}")

# Load matches via data provider
matches_df = load_matches()

# Session state initialization for login tracking
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

st.title("World Cup 2026 Predictions Tournament")

if not st.session_state.logged_in:
    st.subheader("Authentication")
    
    # Form segmentation for login and sign up actions
    auth_mode = st.radio("Choose Action:", ["Login", "Sign Up (New Account)"], horizontal=True)
    
    username = st.text_input("Username").strip()
    pin = st.text_input("Secret PIN (6 Digits)", type="password", max_chars=6)
    
    if st.button("Submit"):
        if username and pin:
            if not (pin.isdigit() and len(pin) == 6):
                st.error("PIN must consist of exactly 6 numeric digits (e.g., 123456).")
            else:
                user_check = check_user(conn, username)
                user_exists = not user_check.empty
                
                if auth_mode == "Login":
                    if user_exists:
                        if user_check.iloc[0]['pin'] == pin:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("Invalid PIN. Please try again.")
                    else:
                        st.error("Username not found. Please select 'Sign Up' to create an account.")
                
                elif auth_mode == "Sign Up (New Account)":
                    if user_exists:
                        st.warning("This Username is already taken! Please choose another one or select 'Login'.")
                    else:
                        create_user(conn, username, pin)
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success("Account created successfully. Welcome!")
                        st.rerun()
        else:
            st.warning("Please enter both your username and PIN.")
else:
    st.sidebar.write(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # Navigation tabs without any emoji icons
    tab1, tab2, tab3 = st.tabs(["Matches & Predictions", "Leaderboard", "Tournament Rules"])

    with tab1:
        st.header("Upcoming Matches")
        
        # Calculate precise Egypt Time (UTC + 3) to ensure exact lock timing on cloud servers
        current_utc_time = datetime.now(timezone.utc)
        current_egypt_time = current_utc_time.replace(tzinfo=None) + timedelta(hours=3)
        
        my_preds = get_user_predictions(conn, st.session_state.username)
        pred_dict = {str(row['match_id']): {
            'predicted_outcome': row['predicted_outcome'],
            'predict_goals': row['predict_goals'],
            'home_score': row['home_score'],
            'away_score': row['away_score']
        } for _, row in my_preds.iterrows()}

        if not matches_df.empty:
            matches_df = matches_df.sort_values(by='match_time')
            matches_df['round_name'] = matches_df['match_id'].apply(get_match_round)
            matches_df['date_group'] = matches_df['match_time'].dt.strftime('%A - %B %d, %Y')
            
            # Hierarchical nested grouping: Round stage followed by calendar day
            for round_name, round_group in matches_df.groupby('round_name', sort=False):
                st.markdown(f"## {round_name}")
                
                for date_str, date_group in round_group.groupby('date_group', sort=False):
                    st.markdown(f"#### {date_str} (Egypt Time)")
                    
                    for index, row in date_group.iterrows():
                        match_id = str(row['match_id'])
                        home = row['home_team']
                        away = row['away_team']
                        m_time = row['match_time']
                        
                        # Close and hide form view dynamically when current Egypt time passes kickoff time
                        if current_egypt_time < m_time:
                            with st.expander(f"{home} vs {away} ({m_time.strftime('%H:%M')} Egypt Time)"):
                                
                                # Fetch flags early for the UI banner
                                home_flag = get_team_flag(home) or "https://via.placeholder.com/80x50.png?text=Flag"
                                away_flag = get_team_flag(away) or "https://via.placeholder.com/80x50.png?text=Flag"
                                
                                # OneFootball Style Scoreboard HTML Injection
                                scoreboard_html = f"""
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px; background-color: #262730; border-radius: 10px; margin-bottom: 20px;">
                                    <div style="text-align: center; width: 33%;">
                                        <img src="{home_flag}" width="60" style="border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                                        <p style="margin: 10px 0 0 0; font-weight: bold; font-size: 16px; color: white;">{home}</p>
                                    </div>
                                    <div style="text-align: center; width: 33%;">
                                        <p style="margin: 0; font-size: 24px; font-weight: 900; color: #888;">VS</p>
                                    </div>
                                    <div style="text-align: center; width: 33%;">
                                        <img src="{away_flag}" width="60" style="border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                                        <p style="margin: 10px 0 0 0; font-weight: bold; font-size: 16px; color: white;">{away}</p>
                                    </div>
                                </div>
                                """
                                st.markdown(scoreboard_html, unsafe_allow_html=True)
                                
                                saved_po = pred_dict.get(match_id, {}).get('predicted_outcome')
                                po_options = ["home", "draw", "away"]
                                default_idx = po_options.index(saved_po) if saved_po in po_options else 0
                                
                                outcome_label = st.radio(
                                    "Select Match Outcome (+3 Points if correct):",
                                    [f"{home} Win", "Draw", f"{away} Win"],
                                    index=default_idx,
                                    horizontal=True,
                                    key=f"out_{match_id}"
                                )
                                predicted_outcome = "home" if outcome_label == f"{home} Win" else "away" if outcome_label == f"{away} Win" else "draw"
                                
                                saved_pg = pred_dict.get(match_id, {}).get('predict_goals', False)
                                predict_goals = st.checkbox(
                                    "Activate Advanced Score Prediction (High Risk / Reward)", 
                                    value=bool(saved_pg), 
                                    key=f"ch_{match_id}"
                                )
                                
                                pred_home = 0
                                pred_away = 0
                                
                                if predict_goals:
                                    col1, col2 = st.columns(2)
                                    default_home = pred_dict.get(match_id, {}).get('home_score', 0)
                                    default_away = pred_dict.get(match_id, {}).get('away_score', 0)
                                    
                                    with col1:
                                        pred_home = st.number_input(f"{home} Goals", min_value=0, step=1, value=int(default_home if default_home is not None else 0), key=f"h_{match_id}")
                                    with col2:
                                        pred_away = st.number_input(f"{away} Goals", min_value=0, step=1, value=int(default_away if default_away is not None else 0), key=f"a_{match_id}")
                                
                                # Dynamic state action label configuration
                                has_predicted = match_id in pred_dict
                                btn_text = "Update Prediction" if has_predicted else "Save Prediction"
                                
                                if st.button(btn_text, key=f"btn_{match_id}"):
                                    save_user_prediction(conn, st.session_state.username, match_id, predicted_outcome, predict_goals, pred_home, pred_away)
                                    st.success("Prediction saved securely.")
                                    st.rerun()
                    st.markdown("---")

    with tab2:
        st.header("Leaderboard Standings")
        all_preds = get_all_predictions(conn)
        
        leaderboard = {}
        for _, pred in all_preds.iterrows():
            uname = pred['username']
            m_id = str(pred['match_id'])
            p_outcome = pred['predicted_outcome']
            p_goals_enabled = bool(pred['predict_goals'])
            p_home = pred['home_score']
            p_away = pred['away_score']
            
            if uname not in leaderboard:
                leaderboard[uname] = {"Username": uname, "Total Points": 0, "Correct Picks": 0, "Matches Predicted": 0}
            
            match_row = matches_df[matches_df['match_id'].astype(str) == m_id]
            if not match_row.empty:
                actual_h = match_row.iloc[0].get('actual_home_score')
                actual_a = match_row.iloc[0].get('actual_away_score')
                
                if pd.notna(actual_h) and pd.notna(actual_a):
                    pts, is_correct = calculate_score(p_outcome, p_goals_enabled, p_home, p_away, actual_h, actual_a)
                    leaderboard[uname]["Total Points"] += pts
                    if is_correct:
                        leaderboard[uname]["Correct Picks"] += 1
                        
            leaderboard[uname]["Matches Predicted"] += 1

        if leaderboard:
            lb_df = pd.DataFrame(list(leaderboard.values())).sort_values(by="Total Points", ascending=False)
            lb_df.reset_index(drop=True, inplace=True)
            lb_df.index += 1
            st.dataframe(lb_df, use_container_width=True)
        else:
            st.info("No predictions recorded yet.")

    with tab3:
        st.header("Tournament Point System & Rules")
        try:
            with open("data/rules.txt", "r", encoding="utf-8") as f:
                rules_markdown = f.read()
            st.markdown(rules_markdown)
        except Exception as e:
            st.error(f"Error loading tournament rules: {e}")
