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

# Load matches using local data folder configuration
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

    tab1, tab2, tab3 = st.tabs(["Matches & Predictions 📝", "Leaderboard 🏆", "Tournament Rules 📜"])

    with tab1:
        st.header("Upcoming Matches")
        current_time = datetime.now()
        
        my_preds = get_user_predictions(conn, st.session_state.username)
        pred_dict = {str(row['match_id']): {
            'predicted_outcome': row['predicted_outcome'],
            'predict_goals': row['predict_goals'],
            'home_score': row['home_score'],
            'away_score': row['away_score']
        } for _, row in my_preds.iterrows()}

        if not matches_df.empty:
            # Group and sort matches by date formatting
            matches_df = matches_df.sort_values(by='match_time')
            matches_df['date_group'] = matches_df['match_time'].dt.strftime('%A - %B %d, %Y')
            
            for date_str, group in matches_df.groupby('date_group', sort=False):
                st.markdown(f"### 📅 {date_str}")
                
                for index, row in group.iterrows():
                    match_id = str(row['match_id'])
                    home = row['home_team']
                    away = row['away_team']
                    m_time = row['match_time']
                    
                    if current_time < m_time:
                        with st.expander(f"🕒 {home} vs {away} ({m_time.strftime('%H:%M')})"):
                            
                            # Outcome prediction UI (Radio buttons)
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
                            
                            # Optional Goal Prediction UI
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
                                    home_flag = get_team_flag(home)
                                    if home_flag:
                                        st.image(home_flag, width=50)
                                    pred_home = st.number_input(f"{home} Goals", min_value=0, step=1, value=int(default_home if default_home is not None else 0), key=f"h_{match_id}")
                                with col2:
                                    away_flag = get_team_flag(away)
                                    if away_flag:
                                        st.image(away_flag, width=50)
                                    pred_away = st.number_input(f"{away} Goals", min_value=0, step=1, value=int(default_away if default_away is not None else 0), key=f"a_{match_id}")
                            
                            if st.button("Lock Prediction 🔒", key=f"btn_{match_id}"):
                                save_user_prediction(conn, st.session_state.username, match_id, predicted_outcome, predict_goals, pred_home, pred_away)
                                st.success("Prediction locked successfully.")
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
                leaderboard[uname] = {"Username": uname, "Total Points": 0, "Matches Predicted": 0}
            
            match_row = matches_df[matches_df['match_id'].astype(str) == m_id]
            if not match_row.empty:
                actual_h = match_row.iloc[0].get('actual_home_score')
                actual_a = match_row.iloc[0].get('actual_away_score')
                
                if pd.notna(actual_h) and pd.notna(actual_a):
                    pts = calculate_score(p_outcome, p_goals_enabled, p_home, p_away, actual_h, actual_a)
                    leaderboard[uname]["Total Points"] += pts
                        
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
        st.markdown("""
        ### 1. Base Match Outcome Prediction
        * **Correct Outcome (Win/Draw/Loss):** You earn **+3 points**.
        * **Incorrect Outcome:** You earn **0 points**.
        
        ### 2. Advanced Score Prediction (Optional Checkbox)
        If you decide to activate the advanced prediction option for a match, the following calculation applies:
        * **Home Team Goals Correct:** You earn **+2 points**.
        * **Home Team Goals Incorrect:** You earn **-1 point**.
        * **Away Team Goals Correct:** You earn **+2 points**.
        * **Away Team Goals Incorrect:** You earn **-1 point**.
        
        ### 🔥 Special Perfect Score Bonus
        * If you predict **both** the home and away goals perfectly correct, you receive a flat **+5 points** bonus instead of 4 points.
        
        *Note: If you do not activate the Advanced Score option, you will face no penalties or rewards regarding the exact goals scored.*
        """)
