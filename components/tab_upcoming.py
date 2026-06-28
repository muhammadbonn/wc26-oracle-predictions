import streamlit as st
from scripts.utils import get_team_flag
from scripts.db_predictions import save_user_prediction
from components.ui_components import render_scoreboard

def render_upcoming_tab(upcoming_df, pred_dict, conn, username):
    """
    Renders the Upcoming Matches tab with a structured knockout prediction UI.
    Uses unique keys to prevent Streamlit element collision.
    """
    st.header("Upcoming Matches")
    if upcoming_df.empty:
        st.info("No upcoming matches available.")
        return

    first_round = True
    # Group matches by their round name
    for round_name, round_group in upcoming_df.groupby('round_name', sort=False):
        # Determine if it's a knockout stage based on round name
        is_knockout = "Group" not in str(round_name)
        
        with st.expander(round_name, expanded=first_round):
            first_round = False
            first_upcoming_found = False
            
            # Sub-group matches by date
            for date_str, date_group in round_group.groupby('date_group', sort=False):
                st.markdown(f"#### {date_str}")
                for _, row in date_group.iterrows():
                    match_id = str(row['match_id'])
                    # Generate a unique key based on match ID and round to avoid duplicate element errors
                    unique_key = f"{match_id}_{round_name.replace(' ', '_')}"
                    
                    home, away = row['home_team'], row['away_team']
                    m_time = row['match_time']
                    
                    is_first = not first_upcoming_found
                    if is_first: first_upcoming_found = True
                        
                    with st.expander(f"{home} vs {away} ({m_time.strftime('%H:%M')})", expanded=is_first):
                        render_scoreboard(home, away, get_team_flag(home), get_team_flag(away), "VS")
                        
                        # Fetch existing predictions
                        saved_data = pred_dict.get(match_id, {})
                        saved_po = saved_data.get('predicted_outcome')
                        saved_pens = bool(saved_data.get('predict_penalties'))
                        
                        # Define outcome options based on match stage
                        if is_knockout:
                            outcome_options = [f"{home} Win", f"{away} Win", "Pens (Home Win)", "Pens (Away Win)"]
                            # Logic for setting the default radio index
                            default_idx = 0
                            if saved_po == 'home' and saved_pens: default_idx = 2
                            elif saved_po == 'away' and saved_pens: default_idx = 3
                            elif saved_po == 'away': default_idx = 1
                        else:
                            outcome_options = [f"{home} Win", "Draw", f"{away} Win"]
                            default_idx = outcome_options.index(f"{home} Win" if saved_po == 'home' else f"{away} Win" if saved_po == 'away' else "Draw") if saved_po else 0
                        
                        # User selects the match outcome
                        outcome_label = st.radio("Select Outcome:", outcome_options, index=default_idx, horizontal=True, key=f"out_{unique_key}")
                        
                        # Parse user selection
                        if is_knockout:
                            predicted_outcome = "home" if "home" in outcome_label.lower() else "away"
                            predict_pens = "Pens" in outcome_label
                        else:
                            predicted_outcome = "home" if outcome_label == f"{home} Win" else "away" if outcome_label == f"{away} Win" else "draw"
                            predict_pens = False
                        
                        # Advanced Prediction Section
                        predict_goals = st.checkbox("Activate Advanced Score Prediction", key=f"ch_{unique_key}")
                        
                        pred_home, pred_away, pred_hp, pred_ap = 0, 0, 0, 0
                        if predict_goals:
                            col1, col2 = st.columns(2)
                            pred_home = col1.number_input("Home Goals", min_value=0, step=1, value=int(saved_data.get('home_score', 0)), key=f"h_{unique_key}")
                            pred_away = col2.number_input("Away Goals", min_value=0, step=1, value=int(saved_data.get('away_score', 0)), key=f"a_{unique_key}")
                            
                            if is_knockout:
                                col3, col4 = st.columns(2)
                                pred_hp = col3.number_input("Home Pens", min_value=0, step=1, value=int(saved_data.get('home_penalties_score', 0)), key=f"hp_{unique_key}")
                                pred_ap = col4.number_input("Away Pens", min_value=0, step=1, value=int(saved_data.get('away_penalties_score', 0)), key=f"ap_{unique_key}")
                        
                        # Save prediction logic
                        if st.button("Save Prediction", key=f"btn_{unique_key}"):
                            save_user_prediction(conn, username, match_id, predicted_outcome, predict_goals, 
                                                 pred_home, pred_away, predict_pens, pred_hp, pred_ap)
                            st.success("Prediction saved successfully!")
                            st.rerun()
