import streamlit as st
import pandas as pd
from scripts.utils import calculate_score
# Import the history function to reuse it inside the leaderboard user search
from components.tab_history import render_history_tab

def render_leaderboard_tab(all_preds, matches_df, past_df):
    """Renders the Leaderboard standings table and a user search section."""
    st.header("Leaderboard Standings")
    
    if all_preds.empty:
        st.info("No predictions recorded yet.")
        return

    # Calculate points and stats for all users
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
                if is_correct: leaderboard[uname]["Correct Picks"] += 1
                leaderboard[uname]["Finished Predictions"] += 1
        
        leaderboard[uname]["Total Predicted"] += 1

    # Format data into a list for the DataFrame
    lb_list = []
    for uname, stats in leaderboard.items():
        if stats["Finished Predictions"] > 0:
            stats["Live Accuracy (%)"] = round((stats["Correct Picks"] / stats["Finished Predictions"]) * 100, 1)
        lb_list.append(stats)
    
    # Create DataFrame and sort
    lb_df = pd.DataFrame(lb_list)
    lb_df = lb_df.sort_values(by=["Total Points", "Live Accuracy (%)"], ascending=[False, False])
    lb_df["Live Accuracy (%)"] = lb_df["Live Accuracy (%)"].astype(str) + " %"
    lb_df.reset_index(drop=True, inplace=True)
    lb_df.index += 1

    # 1. Display the traditional wide DataFrame
    st.dataframe(lb_df, use_container_width=True)

    # 2. Display the search section to view specific user history
    st.markdown("---")
    st.subheader("Search User Predictions")
    
    user_list = lb_df["Username"].tolist()
    if user_list:
        selected_user = st.selectbox("Select a player to view their history:", user_list)
        
        if selected_user:
            with st.expander(f"View {selected_user}'s History"):
                # Filter predictions and matches for the selected user
                user_preds = all_preds[all_preds['username'] == selected_user]
                user_past_df = past_df[past_df['match_id'].astype(str).isin(user_preds['match_id'].astype(str))]
                user_pred_dict = {str(r['match_id']): r for _, r in user_preds.iterrows()}
                
                if not user_past_df.empty:
                    # Pass show_header=False to avoid duplicate titles
                    render_history_tab(user_past_df, user_pred_dict, show_header=False)
                else:
                    st.info("No past predictions yet for this user.")
