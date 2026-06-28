import streamlit as st
import pandas as pd
from scripts.utils import get_team_flag
from scripts.db_predictions import save_user_prediction
from components.ui_components import render_scoreboard

def render_upcoming_tab(upcoming_df, pred_dict, conn, username):
    st.header("Upcoming Matches")
    if upcoming_df.empty:
        st.info("No upcoming matches available.")
        return

    unique_matches = upcoming_df.drop_duplicates(subset=['match_id'])

    for round_name, round_group in unique_matches.groupby('round_name', sort=False):
        is_knockout = "Group" not in str(round_name)
        
        with st.expander(round_name, expanded=True):
            for _, row in round_group.iterrows():
                home = str(row['home_team']) if pd.notna(row['home_team']) else "TBD"
                away = str(row['away_team']) if pd.notna(row['away_team']) else "TBD"
                match_id = str(row['match_id'])
                unique_key = f"{match_id}_{round_name.replace(' ', '_')}"
                
                with st.expander(f"{home} vs {away}"):
                    render_scoreboard(home, away, get_team_flag(home), get_team_flag(away), "VS")
                    
                    saved_data = pred_dict.get(match_id, {})
                    
                    if is_knockout:
                        # 1. Winner selection
                        winner = st.radio("Select Winner:", [home, away], horizontal=True, key=f"win_{unique_key}", index=0 if saved_data.get('predicted_outcome') == 'home' else 1 if saved_data.get('predicted_outcome') == 'away' else 0)
                        # 2. Single checkbox for penalties
                        is_pens = st.checkbox("Win via Penalties", value=saved_data.get('predict_penalties', False), key=f"pens_{unique_key}")
                        
                        predicted_outcome = "home" if winner == home else "away"
                        predict_pens = is_pens
                    else:
                        outcome = st.radio("Outcome:", [f"{home} Win", "Draw", f"{away} Win"], horizontal=True, key=f"out_{unique_key}")
                        predicted_outcome = "home" if home in outcome else ("away" if away in outcome else "draw")
                        predict_pens = False

                    # Advanced Section
                    predict_goals = st.checkbox("Activate Advanced Score Prediction", key=f"ch_{unique_key}")
                    pred_home, pred_away, pred_hp, pred_ap = 0, 0, 0, 0
                    
                    if predict_goals:
                        c1, c2 = st.columns(2)
                        pred_home = c1.number_input(f"{home} Goals", min_value=0, step=1, value=int(saved_data.get('home_score', 0)), key=f"h_{unique_key}")
                        pred_away = c2.number_input(f"{away} Goals", min_value=0, step=1, value=int(saved_data.get('away_score', 0)), key=f"a_{unique_key}")
                        if is_knockout:
                            c3, c4 = st.columns(2)
                            pred_hp = c3.number_input(f"{home} Pens", min_value=0, step=1, value=int(saved_data.get('home_penalties_score', 0)), key=f"hp_{unique_key}")
                            pred_ap = c4.number_input(f"{away} Pens", min_value=0, step=1, value=int(saved_data.get('away_penalties_score', 0)), key=f"ap_{unique_key}")

                    # Dynamic Button: Save or Update
                    is_updated = match_id in pred_dict
                    btn_label = "Update Prediction" if is_updated else "Save Prediction"
                    
                    if st.button(btn_label, key=f"btn_{unique_key}"):
                        save_user_prediction(conn, username, match_id, predicted_outcome, predict_goals, 
                                             pred_home, pred_away, predict_pens, pred_hp, pred_ap)
                        st.success("Prediction saved!" if not is_updated else "Prediction updated!")
                        st.rerun()
