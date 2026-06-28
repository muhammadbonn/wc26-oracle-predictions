import streamlit as st
import pandas as pd
from scripts.utils import calculate_score
from components.tab_history import render_history_tab

def render_second_chance_tab(all_preds, matches_df, past_df):
    """Renders a separate leaderboard only for Knockout stage matches (match_id > 72)."""
    st.header("Second Chance Standings (Knockouts Only)")
    
    # Filter matches and predictions to include only post-group stage (match_id > 72)
    ko_matches = matches_df[matches_df['match_id'].astype(int) > 72]
    ko_match_ids = ko_matches['match_id'].astype(str).tolist()
    
    ko_preds = all_preds[all_preds['match_id'].astype(str).isin(ko_match_ids)]
    
    if ko_preds.empty:
        st.info("No knockout stage predictions recorded yet.")
        return

    # Calculate points and stats for all users based on filtered matches
    leaderboard = {}
    for _, pred in ko_preds.iterrows():
        uname = pred['username']
        m_id = str(pred['match_id'])
        
        if uname not in leaderboard:
            leaderboard[uname] = {
                "Username": uname, 
                "Total Points": 0, 
                "Correct Picks": 0, 
                "Finished Predictions": 0, 
                "Live Accuracy (%)": 0.0,
                "Total Predicted": 0
            }
        
        leaderboard[uname]["Total Predicted"] += 1
        
        match_row = ko_matches[ko_matches['match_id'].astype(str) == m_id]
        if not match_row.empty:
            match_data = match_row.iloc[0]
            actual_h = match_data.get('actual_home_score')
            actual_a = match_data.get('actual_away_score')
            
            if pd.notna(actual_h) and pd.notna(actual_a):
                is_knockout = "Group" not in str(match_data.get('round_name', ''))
                
                # Updated 13-parameter call
                pts = calculate_score(
                    pred['predicted_outcome'], 
                    bool(pred['predict_goals']), 
                    pred.get('home_score', 0), 
                    pred.get('away_score', 0),
                    pred.get('predict_penalties', False),
                    pred.get('home_penalties_score', 0),
                    pred.get('away_penalties_score', 0),
                    actual_h, actual_a,
                    match_data.get('actual_penalties', False),
                    match_data.get('actual_hp', 0),
                    match_data.get('actual_ap', 0),
                    is_knockout
                )
                
                leaderboard[uname]["Total Points"] += pts
                if pts > 0: 
                    leaderboard[uname]["Correct Picks"] += 1
                leaderboard[uname]["Finished Predictions"] += 1

    lb_list = []
    for uname, stats in leaderboard.items():
        if stats["Finished Predictions"] > 0:
            stats["Live Accuracy (%)"] = round((stats["Correct Picks"] / stats["Finished Predictions"]) * 100, 1)
        lb_list.append(stats)
    
    lb_df = pd.DataFrame(lb_list)
    if lb_df.empty:
        st.info("No knockout stage matches finished yet.")
        return
        
    lb_df = lb_df.sort_values(by=["Total Points", "Live Accuracy (%)"], ascending=[False, False])
    lb_df["Live Accuracy (%)"] = lb_df["Live Accuracy (%)"].astype(str) + " %"
    
    # Enforce the specific column order
    columns_to_show = [
        "Username", 
        "Total Points", 
        "Correct Picks", 
        "Finished Predictions", 
        "Live Accuracy (%)", 
        "Total Predicted"
    ]
    lb_df = lb_df[columns_to_show]
    
    lb_df.reset_index(drop=True, inplace=True)
    lb_df.index += 1

    # Render the dataframe
    st.dataframe(lb_df, use_container_width=True)

    # Search section for viewing specific user history (filtered for knockouts)
    st.markdown("---")
    st.subheader("Search User Knockout Predictions")
    
    user_list = lb_df["Username"].tolist()
    if user_list:
        selected_user = st.selectbox("Select a player to view their knockout history:", user_list, key="sc_selectbox")
        
        if selected_user:
            with st.expander(f"View {selected_user}'s Knockout History"):
                user_preds = ko_preds[ko_preds['username'] == selected_user]
                user_past_df = past_df[(past_df['match_id'].astype(str).isin(user_preds['match_id'].astype(str))) & (past_df['match_id'].astype(int) > 72)]
                
                # Added .to_dict() to prevent Truth Value ambiguous error
                user_pred_dict = {str(r['match_id']): r.to_dict() for _, r in user_preds.iterrows()}
                
                if not user_past_df.empty:
                    render_history_tab(user_past_df, user_pred_dict, show_header=False)
                else:
                    st.info("No knockout past predictions yet for this user.")
