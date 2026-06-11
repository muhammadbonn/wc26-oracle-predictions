from sqlalchemy import text

def check_user(conn, username):
    # Query database to verify if user exists
    return conn.query("SELECT * FROM users WHERE username = :u", params={"u": username})

def create_user(conn, username, pin):
    # Insert new user record into database
    with conn.session as session:
        session.execute(text("INSERT INTO users (username, pin) VALUES (:u, :p)"), {"u": username, "p": pin})
        session.commit()

def get_user_predictions(conn, username):
    # Retrieve existing predictions for specific user to populate fields
    return conn.query("SELECT match_id, home_score, away_score FROM predictions WHERE username = :u", params={"u": username})

def save_user_prediction(conn, username, match_id, home_score, away_score):
    # Insert or update prediction data securely using database constraints
    with conn.session as session:
        query = text("""
            INSERT INTO predictions (username, match_id, home_score, away_score) 
            VALUES (:u, :m, :h, :a) 
            ON CONFLICT (username, match_id) 
            DO UPDATE SET home_score = :h, away_score = :a;
        """)
        session.execute(query, {"u": username, "m": match_id, "h": home_score, "a": away_score})
        session.commit()

def get_all_predictions(conn):
    # Load all records to calculate standings dynamically
    return conn.query("SELECT * FROM predictions")
