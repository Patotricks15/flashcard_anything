import sqlite3
import hashlib
from datetime import datetime, timedelta
import pandas as pd

# Function to create a connection to SQLite
def create_connection():
    """
    Creates and returns a connection to the local SQLite database (my_database.db).
    """
    conn = sqlite3.connect('my_database.db')
    return conn

# ------------------ Security and Hashing ------------------
def make_hashes(password):
    """
    Generates a SHA-256 hash from a string (password).
    """
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """
    Compares the hash of a password with the stored hash.
    Returns the hash if they match or False otherwise.
    """
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# ------------------ Table Creation ------------------
def create_tables():
    """
    Creates tables in the SQLite database if they do not exist.
    """
    conn = create_connection()
    c = conn.cursor()

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userName TEXT NOT NULL,
            userPassword TEXT NOT NULL
        );
    ''')

    # User searches table
    c.execute('''
        CREATE TABLE IF NOT EXISTS usersSearch(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userName TEXT NOT NULL,
            search TEXT NOT NULL,
            flashcard_name TEXT,
            flashcard_text TEXT,
            timeStamp TEXT,
            initialDate TEXT,
            finalDate TEXT,
            language TEXT
        );
    ''')

    # Table to store flashcard study logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS flashcardStudyLog(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userName TEXT NOT NULL,
            selectedSearch TEXT NOT NULL,
            flashcardName TEXT NOT NULL,
            flashcardText TEXT NOT NULL,
            datetimeLastStudy DATETIME,
            datetimeNextStudy DATETIME,
            studyInterval REAL,
            easeFactor REAL,
            reps INTEGER
        );
    ''')

    # Table to store uploaded documents (e.g., PDFs)
    c.execute('''
        CREATE TABLE IF NOT EXISTS userDocuments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userName TEXT NOT NULL,
            fileName TEXT,
            fileContent BLOB
        );
    ''')

    conn.commit()
    conn.close()

# ------------------ User Functions ------------------
def add_userdata(username, password):
    """
    Adds a user to the 'users' table.
    """
    conn = create_connection()
    c = conn.cursor()
    hashed_password = make_hashes(password)
    c.execute('INSERT INTO users(userName, userPassword) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    conn.close()

def login_user(username, password):
    """
    Checks if a user with the provided username and password exists.
    Returns the user data if exists, or an empty list otherwise.
    """
    conn = create_connection()
    c = conn.cursor()
    hashed_password = make_hashes(password)
    c.execute('SELECT * FROM users WHERE userName = ? AND userPassword = ?', (username, hashed_password))
    data = c.fetchall()
    conn.close()
    return data

# ------------------ Search and Flashcard Functions ------------------
def add_usersearch(username, search, flashcard_name, flashcard_text, timestamp):
    """
    Adds a user search with flashcard_name, flashcard_text and other information.
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO usersSearch(
            userName, 
            search, 
            flashcardName,
            flashcardText, 
            timeStamp 
        ) VALUES (?, ?, ?, ?, ?)
    ''', (username, search, flashcard_name, flashcard_text, timestamp))
    conn.commit()
    conn.close()

def query_searches_flashcards(username):
    """
    Returns distinct searches that already have flashcards studied by the user.
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT(selectedSearch) 
        FROM flashcardStudyLog
        WHERE userName = ?
    ''', (username,))
    data = c.fetchall()
    conn.close()
    return data

def query_flashcards(username, search):
    """
    Returns a list of flashcards (flashcardName and flashcardText) for a specific user search.
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute('''
        SELECT flashcardName, flashcardText 
        FROM flashcardStudyLog 
        WHERE userName = ? AND selectedSearch = ?
    ''', (username, search))
    data = c.fetchall()
    conn.close()
    return data


def add_flashcard_study(username, selected_search, flashcard_name, flashcard_text):
    """
    Adds a flashcard to the flashcardStudyLog table,
    but first checks if it already exists (for the same userName and selectedSearch).
    Returns True if inserted, False if not inserted (already exists).
    """
    conn = create_connection()
    c = conn.cursor()

    # 1. Check if the flashcard already exists
    check_query = """
        SELECT COUNT(*)
        FROM flashcardStudyLog
        WHERE userName = ?
          AND selectedSearch = ?
          AND flashcardName = ?
    """
    c.execute(check_query, (username, selected_search, flashcard_name))
    (count_existing,) = c.fetchone()

    # If it already exists, do not insert again
    if count_existing > 0:
        print(f"Flashcard '{flashcard_name}' for search '{selected_search}' already exists. It will not be added.")
        conn.close()
        return False

    # 2. If it does not exist, insert it with initial datetimeNextStudy as now
    initial_datetime_now = None
    initial_next_study_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Due immediately
    insert_query = """
    INSERT INTO flashcardStudyLog (
        userName,
        selectedSearch,
        flashcardName,
        flashcardText,
        datetimeLastStudy,
        datetimeNextStudy,
        studyInterval,
        easeFactor,
        reps
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    c.execute(insert_query, (
        username, 
        selected_search, 
        flashcard_name, 
        flashcard_text, 
        initial_datetime_now,  # No last study yet
        initial_next_study_date,  # Set nextStudyDate to now
        1, 
        2.5, 
        0
    ))
    
    conn.commit()
    conn.close()
    return True

def get_flashcards_study(username, selected_search):
    """
    Returns the list of flashcards ready for study:
    - Have not been studied today;
    - Ordered by the number of repetitions (ASC).
    """
    conn = create_connection()
    c = conn.cursor()
    query = """
    SELECT 
        flashcardName, 
        flashcardText, 
        MAX(datetimeLastStudy) as lastStudied, 
        MAX(studyInterval) as studyInterval, 
        MAX(easeFactor) as easeFactor, 
        count(*) as current_reps
    FROM 
        flashcardStudyLog
    WHERE 
        userName = ?
        AND selectedSearch = ?
        AND DATE(datetimeNextStudy) <= DATETIME('now', 'localtime', '-1 minute')
        AND flashcardName NOT IN (
            SELECT flashcardName 
            FROM flashcardStudyLog
            WHERE DATE(datetimeNextStudy) > DATETIME('now', 'localtime')
        )
    GROUP BY 
        flashcardName
    ORDER BY 
        current_reps ASC;
    """
    c.execute(query, (username, selected_search))
    flashcards = c.fetchall()
    conn.close()
    return flashcards

def update_flashcard_study(username, selected_search, flashcard_name, flashcard_text, grade, current_interval, current_ease_factor, current_reps):
    """
    Updates the study log of a flashcard by calculating new intervals and ease factors.
    """
    conn = create_connection()
    c = conn.cursor()

    # Calculation of the new interval
    if grade >= 3:
        current_reps += 1
        if current_reps == 1:
            new_interval = 1
        elif current_reps == 2:
            new_interval = 2
        else:
            new_interval = current_interval * current_ease_factor
    else:
        current_reps = 0
        new_interval = 1

    # Adjustment of the ease factor
    ease_delta = {5: 1.15, 4: 1.10, 3: 1.0, 2: 0.9, 1: 0.8}
    new_ease_factor = max(1.3, current_ease_factor * ease_delta[grade])
    
    # Next study date
    new_due_date = datetime.now() + timedelta(days=new_interval)

    query = """
    INSERT INTO flashcardStudyLog (
        userName, 
        selectedSearch, 
        flashcardName, 
        flashcardText, 
        datetimeLastStudy,
        datetimeNextStudy,
        studyInterval, 
        easeFactor, 
        reps
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    c.execute(query, (
        username, 
        selected_search, 
        flashcard_name, 
        flashcard_text,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        new_due_date, 
        new_interval, 
        new_ease_factor, 
        current_reps
    ))
    conn.commit()
    conn.close()

def insert_study_log(username, selected_search, flashcard_name, flashcard_text):
    """
    Inserts a simple study log for a flashcard (without SM-2 calculation).
    """
    conn = create_connection()
    c = conn.cursor()
    insert_query = """
    INSERT INTO flashcardStudyLog (
        userName, 
        selectedSearch, 
        flashcardName, 
        flashcardText
    )
    VALUES (?, ?, ?, ?);
    """
    c.execute(insert_query, (username, selected_search, flashcard_name, flashcard_text))
    conn.commit()
    conn.close()

# ------------------ Function to Store File in DB ------------------
def store_document(username, file_name, file_content):
    """
    Stores a document (e.g., PDF) as a BLOB in the 'userDocuments' table.
    - file_content should be in bytes format.
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO userDocuments(userName, fileName, fileContent)
        VALUES (?, ?, ?)
    ''', (username, file_name, file_content))
    conn.commit()
    conn.close()

# ------------------ Security and Hashing 2 ------------------

def create_usertable():
    """
    Creates the 'users' table to store users (if it does not exist).
    """
    conn = create_connection()
    c = conn.cursor()

    # UNIQUE ensures that no two users have the same name
    c.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userName TEXT UNIQUE NOT NULL,
            userPassword TEXT NOT NULL
        );
    ''')

    conn.commit()
    conn.close()

def make_hashes(password: str) -> str:
    """
    Returns the SHA-256 hash of the provided password string.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def add_userdata(username, password):
    """
    Adds a new user to the 'users' table (unique username, userPassword hashed).
    """
    conn = create_connection()
    c = conn.cursor()

    hashed_password = make_hashes(password)
    c.execute('INSERT INTO users(userName, userPassword) VALUES (?, ?)', (username, hashed_password))

    conn.commit()
    conn.close()

def login_user(username, password):
    """
    Checks if a user with the corresponding username and hashed password exists.
    Returns True if login is successful, or False otherwise.
    """
    conn = create_connection()
    c = conn.cursor()

    hashed_password = make_hashes(password)
    query = 'SELECT * FROM users WHERE userName = ? AND userPassword = ?'
    c.execute(query, (username, hashed_password))
    result = c.fetchone()

    conn.close()
    return True if result else False

def user_exists(username):
    """
    Checks if a given username already exists in the database.
    Returns True if it exists, False otherwise.
    """
    conn = create_connection()
    c = conn.cursor()

    query = 'SELECT * FROM users WHERE userName = ?'
    c.execute(query, (username,))
    result = c.fetchone()

    conn.close()
    return True if result else False

# ------------------ Function user informations ------------------
def get_daily_reviews(user_name: str) -> pd.DataFrame:
    """
    Returns a DataFrame with columns [study_date, reviews]
    representing the number of reviews per day (DATE).
    """
    conn = create_connection()
    query = """
        SELECT 
            DATE(datetimeLastStudy) AS study_date,
            COUNT(*) AS reviews
        FROM flashcardStudyLog
        WHERE userName = ?
        AND
        reps > 0
        GROUP BY DATE(datetimeLastStudy)
        ORDER BY DATE(datetimeLastStudy);
    """
    df = pd.read_sql_query(query, conn, params=(user_name,))
    conn.close()
    return df

def get_daily_reviews_current_year(user_name: str) -> pd.DataFrame:
    """
    Returns a DataFrame with columns [study_date, reviews],
    representing the number of reviews per day for the current year only.
    """
    conn = create_connection()
    query = """
        SELECT 
            DATE(datetimeLastStudy) AS study_date,
            COUNT(*) AS reviews
        FROM flashcardStudyLog
        WHERE 
            userName = ?
            AND reps > 0
            AND datetimeLastStudy >= date('now','-365 day')
        GROUP BY DATE(datetimeLastStudy)
        ORDER BY DATE(datetimeLastStudy);
    """
    df = pd.read_sql_query(query, conn, params=(user_name,))
    conn.close()
    return df

def get_user_stats(user_name: str) -> dict:
    """
    Returns a dictionary containing the user's general metrics:
    {
        'total_reviews': ...,
        'distinct_cards': ...,
        'avg_ease_factor': ...,
        'avg_interval': ...
    }
    """
    conn = create_connection()
    query = """
        SELECT 
            DISTINCT COUNT(flashcardName) AS total_reviews,
            COUNT(DISTINCT flashcardName) AS distinct_cards,
            AVG(easeFactor) AS avg_ease_factor,
            AVG(studyInterval) AS avg_interval
        FROM flashcardStudyLog
        WHERE userName = ?;
    """
    c = conn.cursor()
    c.execute(query, (user_name,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            'total_reviews': row[0] if row[0] else 0,
            'distinct_cards': row[1] if row[1] else 0,
            'avg_ease_factor': round(row[2], 2) if row[2] else 0.0,
            'avg_interval': round(row[3], 2) if row[3] else 0.0
        }
    else:
        return {
            'total_reviews': 0,
            'distinct_cards': 0,
            'avg_ease_factor': 0.0,
            'avg_interval': 0.0
        }
