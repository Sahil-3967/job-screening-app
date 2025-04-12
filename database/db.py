
import sqlite3

def init_db():
    conn = sqlite3.connect('job_screening.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            score REAL,
            resume TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_candidate(name, score, resume_text):
    conn = sqlite3.connect('job_screening.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO candidates (name, score, resume) VALUES (?, ?, ?)', (name, score, resume_text))
    conn.commit()
    conn.close()
