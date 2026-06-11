from sqlalchemy import text

def check_user(conn, username):
    return conn.query("SELECT * FROM users WHERE username = :u", params={"u": username})

def create_user(conn, username, pin):
    with conn.session as session:
        session.execute(text("INSERT INTO users (username, pin) VALUES (:u, :p)"), {"u": username, "p": pin})
        session.commit()

def get_user_predictions(conn, username):
    return conn.query("SELECT match_id, predicted_outcome, predict_goals, home_score, away_score FROM predictions WHERE username = :u", params={"u": username})

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
    return conn.query("SELECT * FROM predictions")
