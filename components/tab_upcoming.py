import streamlit as st
from scripts.utils import get_team_flag
from scripts.db_predictions import save_user_prediction
from components.ui_components import render_scoreboard

def render_upcoming_tab(upcoming_df, pred_dict, conn, username):
    """Renders the Upcoming Matches tab with nested gameweek expanders."""
    st.header("Upcoming Matches")
    if upcoming_df.empty:
        st.info("No upcoming matches available.")
        return

    first_round = True
    for round_name, round_group in upcoming_df.groupby('round_name', sort=False):
        # Each Gameweek is a collapsible section
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
                        # Use the shared UI component for scoreboard
                        render_scoreboard(home, away, get_team_flag(home), get_team_flag(away), "VS")
                        
                        # Prediction Logic
                        saved_data = pred_dict.get(match_id)
                        saved_po = saved_data.get('predicted_outcome') if saved_data else None
                        
                        # Change 'Draw' label to 'Draw & Penalties' for matches after group stage (match_id > 72)
                        draw_label = "Draw & Penalties" if int(match_id) > 72 else "Draw"
                        outcome_options = [f"{home} Win", draw_label, f"{away} Win"]
                        
                        # Set default selected index based on saved prediction
                        default_idx = outcome_options.index(f"{home} Win" if saved_po == 'home' else f"{away} Win" if saved_po == 'away' else draw_label) if saved_po else 0
                        
                        outcome_label = st.radio("Select Outcome:", outcome_options, index=default_idx, horizontal=True, key=f"out_{match_id}")
                        
                        # Save it in the database as "draw" regardless of the label used
                        predicted_outcome = "home" if outcome_label == f"{home} Win" else "away" if outcome_label == f"{away} Win" else "draw"
                        
                        saved_goals_enabled = bool(saved_data.get('predict_goals')) if saved_data else False
                        predict_goals = st.checkbox("Activate Advanced Score Prediction", value=saved_goals_enabled, key=f"ch_{match_id}")
                        
                        pred_home, pred_away = 0, 0
                        if predict_goals:
                            col1, col2 = st.columns(2)
                            saved_h_score = int(saved_data.get('home_score', 0)) if saved_data else 0
                            saved_a_score = int(saved_data.get('away_score', 0)) if saved_data else 0
                            pred_home = col1.number_input(f"{home} Goals", min_value=0, step=1, value=saved_h_score, key=f"h_{match_id}")
                            pred_away = col2.number_input(f"{away} Goals", min_value=0, step=1, value=saved_a_score, key=f"a_{match_id}")
                        
                        # Dynamic Button Text
                        button_text = "Update Prediction" if saved_data else "Save Prediction"
                        
                        # Save button
                        if st.button(button_text, key=f"btn_{match_id}"):
                            save_user_prediction(conn, username, match_id, predicted_outcome, predict_goals, pred_home, pred_away)
                            st.success(f"Prediction {'updated' if saved_data else 'saved'} successfully.")
                            st.rerun()
