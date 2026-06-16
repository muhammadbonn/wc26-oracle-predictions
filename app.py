import streamlit as st
import pandas as pd
from scripts.data_provider import load_matches
from scripts.utils import get_match_round, calculate_score
from scripts.db_predictions import get_user_predictions, get_all_predictions
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

# Load data
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

    # Prepare data
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
            st.header("Leaderboard Standings")
            all_preds = get_all_predictions(conn)
            
            if not all_preds.empty:
                leaderboard = {}
                for _, pred in all_preds.iterrows():
                    uname = pred['username']
                    m_id = str(pred['match_id'])
                    
                    if uname not in leaderboard:
                        leaderboard[uname] = {
                            "Username": uname, "Total Points": 0, "Correct Picks": 0, 
                            "Total Predicted": 0, "Finished Predictions": 0, "Live Accuracy (%)": 0.0
                        }
                    
                    match_row = matches_df[matches_df['match_id'].astype(str) == m_id]
                    if not match_row.empty:
                        actual_h = match_row.iloc[0].get('actual_home_score')
                        actual_a = match_row.iloc[0].get('actual_away_score')
                        
                        if pd.notna(actual_h) and pd.notna(actual_a):
                            pts, is_correct = calculate_score(
                                pred['predicted_outcome'], bool(pred['predict_goals']), 
                                pred['home_score'], pred['away_score'], actual_h, actual_a
                            )
                            leaderboard[uname]["Total Points"] += pts
                            if is_correct:
                                leaderboard[uname]["Correct Picks"] += 1
                            leaderboard[uname]["Finished Predictions"] += 1
                    
                    leaderboard[uname]["Total Predicted"] += 1

                # Calculate Accuracy and format
                lb_list = []
                for uname, stats in leaderboard.items():
                    if stats["Finished Predictions"] > 0:
                        stats["Live Accuracy (%)"] = round((stats["Correct Picks"] / stats["Finished Predictions"]) * 100, 1)
                    lb_list.append(stats)
                
                lb_df = pd.DataFrame(lb_list)
                lb_df = lb_df.sort_values(by=["Total Points", "Live Accuracy (%)"], ascending=[False, False])
                lb_df["Live Accuracy (%)"] = lb_df["Live Accuracy (%)"].astype(str) + " %"
                
                lb_df.reset_index(drop=True, inplace=True)
                lb_df.index += 1
                st.dataframe(lb_df, use_container_width=True)
            else:
                st.info("No predictions recorded yet.")
                
        with tab4:
            st.header("Tournament Rules")
            try:
                with open("data/rules.txt", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            except:
                st.error("Rules file not found.")
