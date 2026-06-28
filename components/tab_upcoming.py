import streamlit as st
from scripts.utils import get_team_flag
from scripts.db_predictions import save_user_prediction
from components.ui_components import render_scoreboard

def render_upcoming_tab(upcoming_df, pred_dict, conn, username):
    """Renders the Upcoming Matches tab with knockout-friendly prediction logic."""
    st.header("Upcoming Matches")
    if upcoming_df.empty:
        st.info("No upcoming matches available.")
        return

    first_round = True
    for round_name, round_group in upcoming_df.groupby('round_name', sort=False):
        # Identify if it's a knockout round based on the absence of "Group" in the name
        is_knockout = "Group" not in str(round_name)
        
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
                        
                        saved_data = pred_dict.get(match_id)
                        saved_po = saved_data.get('predicted_outcome') if saved_data else None
                        saved_pens = bool(saved_data.get('predict_penalties')) if saved_data else False
                        
                        # Set initial selection
                        if is_knockout:
                            outcome_options = [f"{home} Win", f"{away} Win", f"{home} Win (Pens)", f"{away} Win (Pens)"]
                            default_idx = 0
                            if saved_po == 'home': default_idx = 2 if saved_pens else 0
                            elif saved_po == 'away': default_idx = 3 if saved_pens else 1
                        else:
                            outcome_options = [f"{home} Win", "Draw", f"{away} Win"]
                            default_idx = outcome_options.index(f"{home} Win" if saved_po == 'home' else f"{away} Win" if saved_po == 'away' else "Draw") if saved_po else 0
                        
                        outcome_label = st.radio("Select Outcome:", outcome_options, index=default_idx, horizontal=True, key=f"out_{match_id}")
                        
                        # Logic extraction
                        if is_knockout:
                            predicted_outcome = "home" if "home" in outcome_label.lower() else "away"
                            predict_pens = "(Pens)" in outcome_label
                        else:
                            predicted_outcome = "home" if outcome_label == f"{home} Win" else "away" if outcome_label == f"{away} Win" else "draw"
                            predict_pens = False
                        
                        # Advanced section
                        predict_goals = st.checkbox("Activate Advanced Score Prediction", key=f"ch_{match_id}")
                        
                        pred_home, pred_away, pred_hp, pred_ap = 0, 0, 0, 0
                        if predict_goals:
                            col1, col2 = st.columns(2)
                            pred_home = col1.number_input("Home Goals", min_value=0, step=1, value=int(saved_data.get('home_score', 0)) if saved_data else 0, key=f"h_{match_id}")
                            pred_away = col2.number_input("Away Goals", min_value=0, step=1, value=int(saved_data.get('away_score', 0)) if saved_data else 0, key=f"a_{match_id}")
                            
                            if is_knockout:
                                col3, col4 = st.columns(2)
                                pred_hp = col3.number_input("Home Pens", min_value=0, step=1, value=int(saved_data.get('home_penalties_score', 0)) if saved_data else 0, key=f"hp_{match_id}")
                                pred_ap = col4.number_input("Away Pens", min_value=0, step=1, value=int(saved_data.get('away_penalties_score', 0)) if saved_data else 0, key=f"ap_{match_id}")
                        
                        if st.button("Save Prediction", key=f"btn_{match_id}"):
                            save_user_prediction(conn, username, match_id, predicted_outcome, predict_goals, pred_home, pred_away, predict_pens, pred_hp, pred_ap)
                            st.success("Prediction saved!")
                            st.rerun()
