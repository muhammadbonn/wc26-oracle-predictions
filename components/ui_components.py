import streamlit as st


def render_scoreboard(home, away, home_flag, away_flag, middle_html):
    html = f"""
    <div style="display:flex;justify-content:space-between;
                align-items:center;padding:15px;
                background:#262730;border-radius:10px;">
        <div style="text-align:center;width:33%;">
            <img src="{home_flag}" width="60">
            <p>{home}</p>
        </div>

        <div style="text-align:center;width:33%;">
            {middle_html}
        </div>

        <div style="text-align:center;width:33%;">
            <img src="{away_flag}" width="60">
            <p>{away}</p>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
