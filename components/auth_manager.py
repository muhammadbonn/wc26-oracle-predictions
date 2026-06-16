import streamlit as st
from scripts.db_users import check_user, create_user


def render_authentication(conn):
    st.subheader("Authentication")

    auth_mode = st.radio(
        "Choose Action:",
        ["Login", "Sign Up (New Account)"],
        horizontal=True
    )

    username = st.text_input("Username").strip()
    pin = st.text_input(
        "Secret PIN (6 Digits)",
        type="password",
        max_chars=6
    )

    if st.button("Submit"):
        if not username or not pin:
            st.warning("Please enter both username and PIN.")
            return

        if not (pin.isdigit() and len(pin) == 6):
            st.error("PIN must consist of 6 numeric digits.")
            return

        user_check = check_user(conn, username)
        user_exists = not user_check.empty

        if auth_mode == "Login":
            if user_exists and user_check.iloc[0]["pin"] == pin:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials.")
        else:
            if user_exists:
                st.warning("Username already taken.")
            else:
                create_user(conn, username, pin)
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
