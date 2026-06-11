from sqlalchemy import text

def get_user_predictions(conn, username):
    # Fetch all predictions for a single user without using cache
    return conn.query("SELECT match_id, predicted_outcome, predict_goals, home_score, away_score FROM predictions WHERE username = :u", params={"u": username}, ttl=0)

def save_user_prediction(conn, username, match_id, predicted_outcome, predict_goals, home_score, away_score):
    # Securely upsert a user prediction record using SQL constraints
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
    # Fetch global tournament predictions with low cache retention for leaderboards
    return conn.query("SELECT * FROM predictions", ttl=10)
