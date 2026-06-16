import streamlit as st
import pandas as pd
from scripts.utils import get_team_flag, calculate_score
from scripts.db_predictions import save_user_prediction
from components.ui_components import render_scoreboard

def render_upcoming_tab(upcoming_df, pred_dict, conn, username):
    st.header("Upcoming Matches")
    if upcoming_df.empty:
        st.info("No upcoming matches available.")
        return

    first_round = True
    for round_name, round_group in upcoming_df.groupby('round_name', sort=False):
        with st.expander(round_name, expanded=first_round):
            first_round = False
            first_upcoming_found = False
            for date_str, date_group in round_group.groupby('date_group', sort=False):
                st.markdown(f"#### {date_str}")
                for _, row in date_group.iterrows():
                    match_id = str(row['match_id'])
                    home, away = row['home_team'], row['away_team']
                    m_time = row['match_time']
                    
                    is_first = not first_upcoming_found
                    if is_first: first_upcoming_found = True
                        
                    with st.expander(f"{home} vs {away} ({m_time.strftime('%H:%M')})", expanded=is_first):
                        render_scoreboard(home, away, get_team_flag(home), get_team_flag(away), "VS")
                        
                        outcome_options = [f"{home} Win", "Draw", f"{away} Win"]
                        saved_po = pred_dict.get(match_id, {}).get('predicted_outcome')
                        default_idx = outcome_options.index(f"{home} Win" if saved_po == 'home' else f"{away} Win" if saved_po == 'away' else "Draw") if saved_po else 0
                        
                        outcome_label = st.radio("Select Outcome:", outcome_options, index=default_idx, horizontal=True, key=f"out_{match_id}")
                        predicted_outcome = "home" if outcome_label == f"{home} Win" else "away" if outcome_label == f"{away} Win" else "draw"
                        
                        predict_goals = st.checkbox("Activate Advanced Score Prediction", value=bool(pred_dict.get(match_id, {}).get('predict_goals')), key=f"ch_{match_id}")
                        
                        pred_home, pred_away = 0, 0
                        if predict_goals:
                            col1, col2 = st.columns(2)
                            pred_home = col1.number_input(f"{home} Goals", min_value=0, step=1, value=int(pred_dict.get(match_id, {}).get('home_score', 0)), key=f"h_{match_id}")
                            pred_away = col2.number_input(f"{away} Goals", min_value=0, step=1, value=int(pred_dict.get(match_id, {}).get('away_score', 0)), key=f"a_{match_id}")
                        
                        if st.button("Save/Update Prediction", key=f"btn_{match_id}"):
                            save_user_prediction(conn, username, match_id, predicted_outcome, predict_goals, pred_home, pred_away)
                            st.success("Prediction saved.")
                            st.rerun()

def render_history_tab(past_df, pred_dict):
    st.header("Match History")
    if past_df.empty:
        st.info("No past matches yet.")
        return

    for round_name, round_group in past_df.groupby('round_name', sort=False):
        with st.expander(round_name, expanded=False):
            for _, row in round_group.iterrows():
                match_id = str(row['match_id'])
                home, away = row['home_team'], row['away_team']
                actual_h, actual_a = row.get('actual_home_score'), row.get('actual_away_score')
                mid_html = f'<p style="color: #4CAF50; font-size:36px; font-weight:900;">{int(actual_h)} - {int(actual_a)}</p>' if pd.notna(actual_h) else '<p style="color: #FFA500;">TBD</p>'
                
                with st.expander(f"{home} vs {away}"):
                    render_scoreboard(home, away, get_team_flag(home), get_team_flag(away), mid_html)
                    
                    saved_data = pred_dict.get(match_id)
                    # التعديل هنا: التأكد من تحويل البيانات لقاموس لتفادي الـ ValueError
                    if saved_data is not None:
                        if isinstance(saved_data, pd.Series):
                            saved_data = saved_data.to_dict()
                            
                        po = saved_data.get('predicted_outcome')
                        st.write(f"**Your Prediction:** {po} | Goals: {'Yes' if saved_data.get('predict_goals') else 'No'}")
                        if pd.notna(actual_h):
                            pts, _ = calculate_score(po, saved_data.get('predict_goals'), saved_data.get('home_score'), saved_data.get('away_score'), actual_h, actual_a)
                            st.write(f"**Points Earned:** +{pts}")
                    else:
                        st.warning("No prediction submitted for this match.")

def render_leaderboard_tab(all_preds, matches_df, past_df):
    st.header("Leaderboard Standings")
    leaderboard = {}
    for _, pred in all_preds.iterrows():
        uname = pred['username']
        m_id = str(pred['match_id'])
        if uname not in leaderboard:
            leaderboard[uname] = {"Username": uname, "Total Points": 0, "Correct Picks": 0, "Finished Predictions": 0, "Live Accuracy (%)": 0.0}
        
        match_row = matches_df[matches_df['match_id'].astype(str) == m_id]
        if not match_row.empty:
            actual_h = match_row.iloc[0].get('actual_home_score')
            actual_a = match_row.iloc[0].get('actual_away_score')
            if pd.notna(actual_h):
                pts, is_correct = calculate_score(pred['predicted_outcome'], bool(pred['predict_goals']), pred['home_score'], pred['away_score'], actual_h, actual_a)
                leaderboard[uname]["Total Points"] += pts
                if is_correct: leaderboard[uname]["Correct Picks"] += 1
                leaderboard[uname]["Finished Predictions"] += 1

    lb_list = []
    for uname, stats in leaderboard.items():
        if stats["Finished Predictions"] > 0:
            stats["Live Accuracy (%)"] = round((stats["Correct Picks"] / stats["Finished Predictions"]) * 100, 1)
        lb_list.append(stats)
    
    lb_df = pd.DataFrame(lb_list)
    if not lb_df.empty:
        lb_df = lb_df.sort_values(by=["Total Points", "Live Accuracy (%)"], ascending=[False, False])
        lb_df["Live Accuracy (%)"] = lb_df["Live Accuracy (%)"].astype(str) + " %"
        lb_df.reset_index(drop=True, inplace=True)
        lb_df.index += 1
        
        for i, row in lb_df.iterrows():
            cols = st.columns([1, 3, 2, 2])
            cols[0].write(f"{i+1}")
            cols[1].write(row['Username'])
            cols[2].write(f"{row['Total Points']} pts")
            with cols[3].popover("View History"):
                st.write(f"### {row['Username']}'s Predictions")
                user_preds = all_preds[all_preds['username'] == row['Username']]
                user_past_df = past_df[past_df['match_id'].astype(str).isin(user_preds['match_id'].astype(str))]
                user_pred_dict = {str(r['match_id']): r for _, r in user_preds.iterrows()}
                render_history_tab(user_past_df, user_pred_dict)
    else:
        st.info("No predictions recorded yet.")
