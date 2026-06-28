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
                
                # HTML for the middle section of the scoreboard
                mid_html = f'<p style="color: #4CAF50; font-size:36px; font-weight:900;">{int(actual_h)} - {int(actual_a)}</p>' if pd.notna(actual_h) else '<p style="color: #FFA500;">TBD</p>'
                
                with st.expander(f"{home} vs {away}"):
                    render_scoreboard(home, away, get_team_flag(home), get_team_flag(away), mid_html)
                    
                    saved_data = pred_dict.get(match_id)
                    st.markdown("### Your Prediction Summary")
                    
                    if saved_data is not None:
                        # Convert Pandas Series to dict if necessary
                        if isinstance(saved_data, pd.Series):
                            saved_data = saved_data.to_dict()
                            
                        # Format Predicted Outcome
                        po = saved_data.get('predicted_outcome')
                        
                        # Change 'Draw' label to 'Draw & Penalties' for matches after group stage (match_id > 72)
                        po_text = f"{home} Win" if po == 'home' else f"{away} Win" if po == 'away' else ("Draw & Penalties" if int(match_id) > 72 else "Draw")
                        
                        st.write(f"**Predicted Outcome:** Yes ({po_text})")
                        
                        # Format Predicted Goals
                        goals_enabled = saved_data.get('predict_goals')
                        if goals_enabled:
                            st.write(f"**Predicted Goals:** Yes ({int(saved_data.get('home_score', 0))} - {int(saved_data.get('away_score', 0))})")
                        else:
                            st.write("**Predicted Goals:** No")
                            
                        # Calculate Points
                        if pd.notna(actual_h):
                            pts, _ = calculate_score(po, goals_enabled, saved_data.get('home_score'), saved_data.get('away_score'), actual_h, actual_a)
                            st.write(f"**Points Earned:** +{pts}")
                        else:
                            st.write("**Points Earned:** Waiting for official match results...")
                    else:
                        st.write("**Predicted Outcome:** No")
                        st.write("**Predicted Goals:** No")
                        st.write("**Points Earned:** 0")
