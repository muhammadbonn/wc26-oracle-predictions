import streamlit as st


def render_tabs(conn, matches_df):
    tab1, tab2, tab3, tab4 = st.tabs([
        "Upcoming Matches",
        "Match History",
        "Leaderboard",
        "Tournament Rules"
    ])

    with tab1:
        render_upcoming_matches(conn, matches_df)

    with tab2:
        render_match_history(conn, matches_df)

    with tab3:
        render_leaderboard(conn, matches_df)

    with tab4:
        render_rules()
