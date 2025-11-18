# init_db.py
import sqlite3
import os

# Make sure the folder exists
os.makedirs("userdb", exist_ok=True)

# Connect to database
conn = sqlite3.connect("userdb/user.db")
cursor = conn.cursor()

# ✅ Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    income REAL DEFAULT 0,
    savings_goal REAL DEFAULT 0
)
''')

# ✅ Create transactions table
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()
print("✅ user.db with tables 'users' and 'transactions' is ready.")
