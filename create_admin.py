import sqlite3
import bcrypt

conn = sqlite3.connect("users.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

password = bcrypt.hashpw(
    b"Netapp1!",
    bcrypt.gensalt()
).decode()

try:
    cur.execute(
        "INSERT INTO users(username,password,role) VALUES(?,?,?)",
        ("nas-admin", password, "admin")
    )
    print("Admin created successfully")
except:
    print("Admin already exists")

conn.commit()
conn.close()