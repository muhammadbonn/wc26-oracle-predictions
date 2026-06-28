from sqlalchemy import text

def get_user_predictions(conn, username):
    # تم إضافة الأعمدة الجديدة هنا عشان تترجع مع الداتا
    return conn.query("""
        SELECT match_id, predicted_outcome, predict_goals, home_score, away_score, 
               predict_penalties, home_penalties_score, away_penalties_score 
        FROM predictions WHERE username = :u
    """, params={"u": username}, ttl=0)

def save_user_prediction(conn, username, match_id, predicted_outcome, predict_goals, 
                         home_score, away_score, predict_pens, hp_score, ap_score):
    # تم تحديث الـ Query عشان تشمل الأعمدة الجديدة وتعمل لها Upsert
    with conn.session as session:
        query = text("""
            INSERT INTO predictions 
            (username, match_id, predicted_outcome, predict_goals, home_score, away_score, predict_penalties, home_penalties_score, away_penalties_score) 
            VALUES (:u, :m, :po, :pg, :h, :a, :pp, :hp, :ap) 
            ON CONFLICT (username, match_id) 
            DO UPDATE SET 
                predicted_outcome = :po, 
                predict_goals = :pg, 
                home_score = :h, 
                away_score = :a,
                predict_penalties = :pp,
                home_penalties_score = :hp,
                away_penalties_score = :ap;
        """)
        session.execute(query, {
            "u": username, "m": match_id, "po": predicted_outcome, 
            "pg": predict_goals, "h": home_score, "a": away_score,
            "pp": predict_pens, "hp": hp_score, "ap": ap_score
        })
        session.commit()

def get_all_predictions(conn):
    # Fetch global tournament predictions
    return conn.query("SELECT * FROM predictions", ttl=10)
