import streamlit as st

def render_scoreboard(home, away, home_flag, away_flag, mid_html):
    """Renders the HTML scoreboard component used across tabs."""
    scoreboard_html = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px; background-color: #262730; border-radius: 10px; margin-bottom: 20px;">
        <div style="text-align: center; width: 33%;"><img src="{home_flag}" width="60" style="border-radius: 5px;"><p style="margin: 10px 0 0; color: white; font-weight:bold;">{home}</p></div>
        <div style="text-align: center; width: 33%;">{mid_html}</div>
        <div style="text-align: center; width: 33%;"><img src="{away_flag}" width="60" style="border-radius: 5px;"><p style="margin: 10px 0 0; color: white; font-weight:bold;">{away}</p></div>
    </div>
    """
    st.markdown(scoreboard_html, unsafe_allow_html=True)
