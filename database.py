import sqlite3

conn = sqlite3.connect('casino.db')
cursor = conn.cursor()


async def init_db():    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        name TEXT,
        balance REAL DEFAULT 1000.0
    )''')
    conn.commit()


def get_user_balance(user_id: int):
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


def add_user(user_id: int, username: str, full_name: str):
    cursor.execute("INSERT OR IGNORE INTO users (id, username, name) VALUES (?, ?, ?)", 
                   (user_id, username, full_name))
    conn.commit()


def update_balance(user_id: int, new_balance: float):
    cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
    conn.commit()


def get_leaderboard(limit: int = 10):
    cursor.execute("SELECT name, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
    return cursor.fetchall()
