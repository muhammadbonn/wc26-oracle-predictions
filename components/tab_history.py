import streamlit as st
import pandas as pd
from scripts.utils import get_team_flag, calculate_score
from components.ui_components import render_scoreboard

def render_history_tab(past_df, pred_dict, show_header=True):
    """Renders the Past Matches tab with detailed user prediction summaries."""
    if show_header:
        st.header("Match History")
        
    if past_df.empty:
        st.info("No past matches yet.")
        return

    for round_name, round_group in past_df.groupby('round_name', sort=False):
        # Collapse all history expanders by default
        with st.expander(round_name, expanded=False):
            for _, row in round_group.iterrows():
                match_id = str(row['match_id'])
                home, away = row['home_team'], row['away_team']
                actual_h, actual_a = row.get('actual_home_score'), row.get('actual_away_score')
                
                # Logic to determine if it is a knockout stage
                is_knockout = "Group" not in str(round_name)
                
                # HTML for the scoreboard middle section
                mid_html = f'<p style="color: #4CAF50; font-size:36px; font-weight:900;">{int(actual_h)} - {int(actual_a)}</p>' if pd.notna(actual_h) else '<p style="color: #FFA500;">TBD</p>'
                
                with st.expander(f"{home} vs {away}"):
                    render_scoreboard(home, away, get_team_flag(home), get_team_flag(away), mid_html)
                    
                    saved_data = pred_dict.get(match_id)
                    st.markdown("### Your Prediction Summary")
                    
                    # Safe check for saved_data
                    if saved_data is not None and (isinstance(saved_data, dict) or len(saved_data) > 0):
                        if isinstance(saved_data, pd.Series): 
                            saved_data = saved_data.to_dict()
                            
                        # 1. Display Predicted Outcome
                        po = saved_data.get('predicted_outcome')
                        is_pens = bool(saved_data.get('predict_penalties', False))
                        
                        winner_name = home if po == 'home' else away
                        res_text = f"{winner_name} Win"
                        
                        if is_knockout and is_pens:
                            res_text += " (via Penalties)"
                        elif not is_knockout and po == 'draw':
                            res_text = "Draw"
                        
                        st.write(f"**Predicted Winner:** {res_text}")
                        
                        # Display Penalty Prediction status specifically
                        if is_knockout:
                            st.write(f"**Predicted Penalties:** {'Yes' if is_pens else 'No'}")
                        
                        # 2. Display Advanced Score Prediction
                        if saved_data.get('predict_goals'):
                            st.write(f"**Predicted Score:** {int(saved_data.get('home_score', 0))} - {int(saved_data.get('away_score', 0))}")
                            if is_knockout:
                                st.write(f"**Predicted Pens Score:** {int(saved_data.get('home_penalties_score', 0))} - {int(saved_data.get('away_penalties_score', 0))}")
                        else:
                            st.write("**Advanced Prediction:** Not Activated")
                            
                        # 3. Calculate and display Points
                        if pd.notna(actual_h):
                            pts = calculate_score(
                                po, 
                                saved_data.get('predict_goals', False), 
                                saved_data.get('home_score', 0), 
                                saved_data.get('away_score', 0),
                                is_pens, 
                                saved_data.get('home_penalties_score', 0), 
                                saved_data.get('away_penalties_score', 0),
                                actual_h, actual_a, 
                                row.get('actual_penalties', False), 
                                row.get('actual_hp', 0), 
                                row.get('actual_ap', 0),
                                is_knockout
                            )
                            st.success(f"**Points Earned:** +{pts}")
                        else:
                            st.info("**Points Earned:** Waiting for official match results...")
                    else:
                        st.warning("No prediction submitted for this match.")
