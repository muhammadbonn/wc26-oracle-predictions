from sqlalchemy import text

def check_user(conn, username):
    # Added ttl=0 to bypass Streamlit's cache. 
    # This ensures it always checks the live database for the user.
    return conn.query("SELECT * FROM users WHERE username = :u", params={"u": username}, ttl=0)

def create_user(conn, username, pin):
    with conn.session as session:
        # Added ON CONFLICT DO NOTHING to prevent IntegrityErrors 
        # in case of simultaneous duplicate submissions.
        session.execute(text("""
            INSERT INTO users (username, pin) 
            VALUES (:u, :p) 
            ON CONFLICT (username) DO NOTHING
        """), {"u": username, "p": pin})
        session.commit()

def get_user_predictions(conn, username):
    # Retrieve existing predictions for specific user to populate fields (No cache)
    return conn.query("SELECT match_id, predicted_outcome, predict_goals, home_score, away_score FROM predictions WHERE username = :u", params={"u": username}, ttl=0)

def save_user_prediction(conn, username, match_id, predicted_outcome, predict_goals, home_score, away_score):
    with conn.session as session:
        query = text("""
            INSERT INTO predictions (username, match_id, predicted_outcome, predict_goals, home_score, away_score) 
            VALUES (:u, :m, :po, :pg, :h, :a) 
            ON CONFLICT (username, match_id) 
            DO UPDATE SET predicted_outcome = :po, predict_goals = :pg, home_score = :h, away_score = :a;
        """)
        session.execute(query, {
            "u": username, "m": match_id, "po": predicted_outcome, 
            "pg": predict_goals, "h": home_score, "a": away_score
        })
        session.commit()

def get_all_predictions(conn):
    # Added a short TTL (10 seconds) to ensure the leaderboard is frequently updated
    return conn.query("SELECT * FROM predictions", ttl=10)
