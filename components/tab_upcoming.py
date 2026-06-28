import streamlit as st
import pandas as pd
from scripts.utils import get_team_flag
from scripts.db_predictions import save_user_prediction
from components.ui_components import render_scoreboard

def render_upcoming_tab(upcoming_df, pred_dict, conn, username):
    """
    Renders the Upcoming Matches tab.
    Features:
    - Dynamic Save/Update button.
    - Structured knockout UI (Match winner vs Penalty shootout).
    - Advanced prediction section.
    """
    st.header("Upcoming Matches")
    if upcoming_df.empty:
        st.info("No upcoming matches available.")
        return

    # Ensure unique match entries
    unique_matches = upcoming_df.drop_duplicates(subset=['match_id'])

    for round_name, round_group in unique_matches.groupby('round_name', sort=False):
        is_knockout = "Group" not in str(round_name)
        
        with st.expander(round_name, expanded=True):
            for _, row in round_group.iterrows():
                # Handle potential NaN team names
                home = str(row['home_team']) if pd.notna(row['home_team']) else "TBD"
                away = str(row['away_team']) if pd.notna(row['away_team']) else "TBD"
                match_id = str(row['match_id'])
                unique_key = f"{match_id}_{round_name.replace(' ', '_')}"
                
                with st.expander(f"{home} vs {away}"):
                    render_scoreboard(home, away, get_team_flag(home), get_team_flag(away), "VS")
                    
                    # Fetch saved prediction data
                    saved_data = pred_dict.get(match_id, {})
                    
                    if is_knockout:
                        st.write("Match Winner:")
                        outcome = st.radio("Win:", [f"{home} Win", f"{away} Win"], horizontal=True, key=f"win_{unique_key}")
                        
                        st.write("Penalty Shootout Winner:")
                        pen_outcome = st.radio("Or via Penalties:", [f"Penalties ({home} Win)", f"Penalties ({away} Win)"], horizontal=True, key=f"pen_{unique_key}")
                        
                        # Logic to determine prediction outcome and penalty status
                        if "Penalties" in pen_outcome:
                            predicted_outcome = "home" if home in pen_outcome else "away"
                            predict_pens = True
                        else:
                            predicted_outcome = "home" if home in outcome else "away"
                            predict_pens = False
                    else:
                        outcome = st.radio("Outcome:", [f"{home} Win", "Draw", f"{away} Win"], horizontal=True, key=f"out_{unique_key}")
                        predicted_outcome = "home" if home in outcome else ("away" if away in outcome else "draw")
                        predict_pens = False

                    # Advanced Prediction Section
                    predict_goals = st.checkbox("Activate Advanced Score Prediction", key=f"ch_{unique_key}")
                    if predict_goals:
                        c1, c2 = st.columns(2)
                        pred_home = c1.number_input("Home Goals", min_value=0, step=1, key=f"h_{unique_key}")
                        pred_away = c2.number_input("Away Goals", min_value=0, step=1, key=f"a_{unique_key}")
                        pred_hp, pred_ap = 0, 0
                        if is_knockout:
                            c3, c4 = st.columns(2)
                            pred_hp = c3.number_input("Home Pens", min_value=0, step=1, key=f"hp_{unique_key}")
                            pred_ap = c4.number_input("Away Pens", min_value=0, step=1, key=f"ap_{unique_key}")
                    else:
                        pred_home, pred_away, pred_hp, pred_ap = 0, 0, 0, 0

                    # Determine if this is a new prediction or an update
                    is_updated = match_id in pred_dict
                    btn_label = "Update Prediction" if is_updated else "Save Prediction"
                    
                    # Save/Update Action
                    if st.button(btn_label, key=f"btn_{unique_key}"):
                        save_user_prediction(conn, username, match_id, predicted_outcome, predict_goals, 
                                             pred_home, pred_away, predict_pens, pred_hp, pred_ap)
                        msg = "Prediction updated successfully!" if is_updated else "Prediction saved successfully!"
                        st.success(msg)
                        st.rerun()
