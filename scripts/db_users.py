from sqlalchemy import text

def check_user(conn, username):
    # Query database to check if the username exists without using cache
    return conn.query("SELECT * FROM users WHERE username = :u", params={"u": username}, ttl=0)

def create_user(conn, username, pin):
    # Insert a new user into the database and ignore duplicates safely
    with conn.session as session:
        session.execute(text("""
            INSERT INTO users (username, pin) 
            VALUES (:u, :p) 
            ON CONFLICT (username) DO NOTHING
        """), {"u": username, "p": pin})
        session.commit()
