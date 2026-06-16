import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from scripts.data_provider import load_matches
from scripts.utils import get_team_flag, calculate_score, get_match_round
from scripts.db_users import check_user, create_user
from scripts.db_predictions import get_user_predictions, save_user_prediction, get_all_predictions

# Page configuration
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
        st.header("Tournament Matches")
        
        current_egypt_time = pd.Timestamp.now() + pd.Timedelta(hours=3)
        
        my_preds = get_user_predictions(conn, st.session_state.username)
        
        # FIXED: Extracting values into a standard dictionary to prevent Pandas ValueError
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
            
            first_upcoming_found = False
            
            for round_name, round_group in matches_df.groupby('round_name', sort=False):
                st.markdown(f"## {round_name}")
                for date_str, date_group in round_group.groupby('date_group', sort=False):
                    st.markdown(f"#### {date_str}")
                    for _, row in date_group.iterrows():
                        match_id = str(row['match_id'])
                        home = row['home_team'] if pd.notna(row['home_team']) else "TBD"
                        away = row['away_team'] if pd.notna(row['away_team']) else "TBD"
                        m_time = row['match_time']
                        
                        home_flag = get_team_flag(home) or "https://via.placeholder.com/80x50.png?text=Flag"
                        away_flag = get_team_flag(away) or "https://via.placeholder.com/80x50.png?text=Flag"
                        
                        scoreboard_html = f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px; background-color: #262730; border-radius: 10px; margin-bottom: 20px;">
                            <div style="text-align: center; width: 33%;"><img src="{home_flag}" width="60" style="border-radius: 5px;"><p style="margin: 10px 0 0; color: white; font-weight:bold;">{home}</p></div>
                            <div style="text-align: center; width: 33%;"><p style="margin: 0; color: #888; font-size:24px; font-weight:bold;">VS</p></div>
                            <div style="text-align: center; width: 33%;"><img src="{away_flag}" width="60" style="border-radius: 5px;"><p style="margin: 10px 0 0; color: white; font-weight:bold;">{away}</p></div>
                        </div>
                        """
                        
                        # --- UPCOMING MATCHES (Editable) ---
                        if current_egypt_time < m_time:
                            is_first = not first_upcoming_found
                            if is_first:
                                first_upcoming_found = True
                                
                            with st.expander(f"🟢 {home} vs {away} ({m_time.strftime('%H:%M')}) - Upcoming", expanded=is_first):
                                st.markdown(scoreboard_html, unsafe_allow_html=True)
                                
                                outcome_options = [f"{home} Win", "Draw", f"{away} Win"]
                                saved_po = pred_dict.get(match_id, {}).get('predicted_outcome')
                                default_idx = outcome_options.index(f"{home} Win" if saved_po == 'home' else f"{away} Win" if saved_po == 'away' else "Draw") if saved_po else 0
                                
                                outcome_label = st.radio("Select Outcome (+3 Points):", outcome_options, index=default_idx, horizontal=True, key=f"out_{match_id}")
                                predicted_outcome = "home" if outcome_label == f"{home} Win" else "away" if outcome_label == f"{away} Win" else "draw"
                                
                                saved_pg = pred_dict.get(match_id, {}).get('predict_goals', False)
                                predict_goals = st.checkbox("Activate Advanced Score Prediction", value=bool(saved_pg), key=f"ch_{match_id}")
                                
                                pred_home, pred_away = 0, 0
                                if predict_goals:
                                    col1, col2 = st.columns(2)
                                    default_h = pred_dict.get(match_id, {}).get('home_score', 0)
                                    default_a = pred_dict.get(match_id, {}).get('away_score', 0)
                                    pred_home = col1.number_input(f"{home} Goals", min_value=0, step=1, value=int(default_h if pd.notna(default_h) else 0), key=f"h_{match_id}")
                                    pred_away = col2.number_input(f"{away} Goals", min_value=0, step=1, value=int(default_a if pd.notna(default_a) else 0), key=f"a_{match_id}")
                                
                                btn_text = "Update Prediction" if match_id in pred_dict else "Save Prediction"
                                if st.button(btn_text, key=f"btn_{match_id}"):
                                    save_user_prediction(conn, st.session_state.username, match_id, predicted_outcome, predict_goals, pred_home, pred_away)
                                    st.success("Prediction saved securely.")
                                    st.rerun()
                                    
                        # --- PAST MATCHES (Locked & Read-Only) ---
                        else:
                            with st.expander(f"🔒 {home} vs {away} ({m_time.strftime('%H:%M')}) - Locked", expanded=False):
                                st.markdown(scoreboard_html, unsafe_allow_html=True)
                                
                                saved_data = pred_dict.get(match_id)
                                if saved_data:
                                    po = saved_data.get('predicted_outcome')
                                    po_text = f"{home} Win" if po == 'home' else f"{away} Win" if po == 'away' else "Draw"
                                    st.info(f"**Your Locked Pick:** {po_text}")
                                    
                                    if saved_data.get('predict_goals'):
                                        st.info(f"**Your Locked Score:** {home} {int(saved_data.get('home_score', 0))} - {int(saved_data.get('away_score', 0))} {away}")
                                        
                                    actual_h = row.get('actual_home_score')
                                    actual_a = row.get('actual_away_score')
                                    
                                    if pd.notna(actual_h) and pd.notna(actual_a):
                                        pts, _ = calculate_score(po, saved_data.get('predict_goals'), saved_data.get('home_score'), saved_data.get('away_score'), actual_h, actual_a)
                                        st.success(f"**Official Result:** {home} {int(actual_h)} - {int(actual_a)} {away}")
                                        st.metric("Points Earned", f"+{pts}")
                                    else:
                                        st.warning("Match time has passed. Waiting for official results to be updated...")
                                else:
                                    st.write("*You did not submit a prediction for this match.*")

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
                leaderboard[uname] = {"Username": uname, "Total Points": 0, "Correct Picks": 0, "Matches Predicted": 0, "Accuracy (%)": 0.0}
            
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
            for uname in leaderboard:
                stats = leaderboard[uname]
                if stats["Matches Predicted"] > 0:
                    stats["Accuracy (%)"] = round((stats["Correct Picks"] / stats["Matches Predicted"]) * 100, 1)
            
            lb_df = pd.DataFrame(list(leaderboard.values()))
            lb_df = lb_df.sort_values(by=["Total Points", "Accuracy (%)"], ascending=[False, False])
            
            lb_df["Accuracy (%)"] = lb_df["Accuracy (%)"].astype(str) + " %"
            
            lb_df.reset_index(drop=True, inplace=True)
            lb_df.index += 1
            st.dataframe(lb_df, use_container_width=True)
        else:
            st.info("No predictions recorded yet.")

    with tab3:
        st.header("Tournament Rules")
        try:
            with open("data/rules.txt", "r", encoding="utf-8") as f:
                st.markdown(f.read())
        except:
            st.error("Rules file not found.")
