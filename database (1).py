import sqlite3
import uuid
from datetime import datetime


DB_FILE = "chat_history.db"


# ── SETUP: CREATE TABLE IF NOT EXISTS 

def init_db():
    """Create the chat_history table if it doesn't already exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ── CREATE A NEW SESSION ID 

def new_session_id():
    """Generate a unique session ID for a new chat sitting."""
    return str(uuid.uuid4())


# ── SAVE A MESSAGE 

def save_message(session_id, role, message):
    """
    Save a single message to the database.

    Args:
        session_id (str): unique ID for this chat session
        role (str): "user" or "assistant"
        message (str): the message text
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO chat_history (session_id, role, message) VALUES (?, ?, ?)",
        (session_id, role, message)
    )

    conn.commit()
    conn.close()


# ── GET HISTORY FOR A SESSION 

def get_history(session_id):
    """
    Retrieve all messages for a given session, ordered oldest to newest.

    Returns:
        list of (role, message, timestamp) tuples
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role, message, timestamp FROM chat_history WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,)
    )

    history = cursor.fetchall()
    conn.close()
    return history


# ── GET ALL PAST SESSIONS 

def get_all_sessions():
    """
    Get a list of all past sessions with their first message and timestamp.
    Used to populate the "past sessions" sidebar.

    Returns:
        list of (session_id, first_message, timestamp) tuples,
        most recent first
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT session_id, message, timestamp
        FROM chat_history
        WHERE role = 'user'
        GROUP BY session_id
        HAVING timestamp = MIN(timestamp)
        ORDER BY timestamp DESC
    """)

    sessions = cursor.fetchall()
    conn.close()
    return sessions


# ── INITIALIZE ON IMPORT 
# Make sure the table exists as soon as this module is imported.
init_db()

