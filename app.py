import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

# Page configuration
st.set_page_config(page_title="World Cup 2026 Predictions", page_icon="⚽", layout="wide")

# Initialize database connection using Supabase URI
db_url = "postgresql://postgres.pjopqzmxaapwmfootrcb:3EK.tt9z_B$9b$G@aws-0-eu-west-3.pooler.supabase.com:5432/postgres"

try:
    conn = st.connection("supabase", type="sql", url=db_url)
except Exception as e:
    st.error(f"Database connection error: {e}")

# GitHub CSV URL for matches data
CSV_URL = "https://raw.githubusercontent.com/muhammadbonn/wc26-data-stats/main/data/wc26_matches.csv"

@st.cache_data(ttl=600)
def load_matches():
    try:
        df = pd.read_csv(CSV_URL)
        df['match_time'] = pd.to_datetime(df['match_time'])
        return df
    except Exception as e:
        st.error(f"Error loading matches: {e}")
        return pd.DataFrame()

def calculate_score(pred_home, pred_away, actual_home, actual_away):
    if pd.isna(actual_home) or pd.isna(actual_away):
        return 0
    actual_home, actual_away = int(actual_home), int(actual_away)
    
    pred_result = "home" if pred_home > pred_away else "away" if pred_away > pred_home else "draw"
    actual_result = "home" if actual_home > actual_away else "away" if actual_away > actual_home else "draw"
    
    points = 0
    if pred_result == actual_result:
        points += 3 # Points for predicting the correct outcome (win/draw)
        if pred_home == actual_home and pred_away == actual_away:
            points += 5 # Bonus points for predicting the exact score
    return points

matches_df = load_matches()

# Session state initialization for login tracking
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

st.title("⚽ World Cup 2026 Predictions Tournament")

if not st.session_state.logged_in:
    st.subheader("Authentication / Registration")
    username = st.text_input("Username").strip()
    
    # Enforce a maximum of 6 characters for the PIN
    pin = st.text_input("Secret PIN (6 Digits)", type="password", max_chars=6)
    
    if st.button("Submit"):
        if username and pin:
            # Validate PIN format strictly (must be numeric and exactly 6 digits)
            if not (pin.isdigit() and len(pin) == 6):
                st.error("❌ PIN must consist of exactly 6 numeric digits (e.g., 123456).")
            else:
                # Query database to check if user already exists
                user_check = conn.query("SELECT * FROM users WHERE username = :u", params={"u": username})
                
                if not user_check.empty:
                    if user_check.iloc[0]['pin'] == pin:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("❌ Invalid PIN. Please try again.")
                else:
                    # Register new account with verified 6-digit PIN
                    with conn.session as session:
                        session.execute(text("INSERT INTO users (username, pin) VALUES (:u, :p)"), {"u": username, "p": pin})
                        session.commit()
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("🎉 Account created successfully. Welcome to the tournament.")
                    st.rerun()
        else:
            st.warning("⚠️ Please enter both your username and PIN.")
else:
    st.sidebar.write(f"👋 Welcome, **{st.session_state.username}**")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    tab1, tab2 = st.tabs(["Matches & Predictions 📝", "Leaderboard 🏆"])

    with tab1:
        st.header("Upcoming Matches")
        current_time = datetime.now()
        
        # Retrieve existing predictions for the logged-in user
        my_preds = conn.query("SELECT match_id, home_score, away_score FROM predictions WHERE username = :u", params={"u": st.session_state.username})
        pred_dict = {str(row['match_id']): {'home': row['home_score'], 'away': row['away_score']} for _, row in my_preds.iterrows()}

        if not matches_df.empty:
            for index, row in matches_df.iterrows():
                match_id = str(row['match_id'])
                home = row['home_team']
                away = row['away_team']
                m_time = row['match_time']
                
                # Check if the match has not started yet to allow predictions or updates
                if current_time < m_time:
                    with st.expander(f"🕒 {home} vs {away} - {m_time.strftime('%Y-%m-%d %H:%M')}"):
                        col1, col2 = st.columns(2)
                        
                        default_home = pred_dict.get(match_id, {}).get('home', 0)
                        default_away = pred_dict.get(match_id, {}).get('away', 0)
                        
                        with col1:
                            pred_home = st.number_input(f"{home} Score", min_value=0, step=1, value=default_home, key=f"h_{match_id}")
                        with col2:
                            pred_away = st.number_input(f"{away} Score", min_value=0, step=1, value=default_away, key=f"a_{match_id}")
                                
                        if st.button("Save Prediction", key=f"btn_{match_id}"):
                            with conn.session as session:
                                query = text("""
                                    INSERT INTO predictions (username, match_id, home_score, away_score) 
                                    VALUES (:u, :m, :h, :a) 
                                    ON CONFLICT (username, match_id) 
                                    DO UPDATE SET home_score = :h, away_score = :a;
                                """)
                                session.execute(query, {"u": st.session_state.username, "m": match_id, "h": pred_home, "a": pred_away})
                                session.commit()
                            st.success("Prediction saved successfully.")
                            st.rerun()

    with tab2:
        st.header("Leaderboard Standings")
        
        # Load all predictions recorded in the database
        all_preds = conn.query("SELECT * FROM predictions")
        
        leaderboard = {}
        for _, pred in all_preds.iterrows():
            uname = pred['username']
            m_id = str(pred['match_id'])
            p_home = pred['home_score']
            p_away = pred['away_score']
            
            if uname not in leaderboard:
                leaderboard[uname] = {"Username": uname, "Total Points": 0, "Correct Picks": 0, "Matches Predicted": 0}
            
            # Match current record database data with real-time GitHub CSV actual data
            match_row = matches_df[matches_df['match_id'].astype(str) == m_id]
            if not match_row.empty:
                actual_h = match_row.iloc[0].get('actual_home_score')
                actual_a = match_row.iloc[0].get('actual_away_score')
                
                # Verify that the actual match outcome is published in CSV
                if pd.notna(actual_h) and pd.notna(actual_a):
                    pts = calculate_score(p_home, p_away, actual_h, actual_a)
                    leaderboard[uname]["Total Points"] += pts
                    if pts >= 3:
                        leaderboard[uname]["Correct Picks"] += 1
                        
            leaderboard[uname]["Matches Predicted"] += 1

        if leaderboard:
            lb_df = pd.DataFrame(list(leaderboard.values())).sort_values(by="Total Points", ascending=False)
            lb_df.reset_index(drop=True, inplace=True)
            lb_df.index += 1
            st.dataframe(lb_df, use_container_width=True)
        else:
            st.info("No predictions recorded yet.")
