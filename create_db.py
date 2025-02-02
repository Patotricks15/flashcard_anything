import sqlite3

def create_empty_db():
    # Connect to a local database
    conn = sqlite3.connect('my_database.db')
    c = conn.cursor()

    # Create the user table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userName TEXT NOT NULL,
            userPassword TEXT NOT NULL
        );
    ''')

    # Create the user search table
    c.execute('''
        CREATE TABLE IF NOT EXISTS usersSearch(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userName TEXT NOT NULL,
            search TEXT NOT NULL,
            flashcardName TEXT,
            flashcardText TEXT,
            timeStamp TEXT
        );
    ''')

        # Create a unique index to avoid inserting duplicate flashcards
    c.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_user_search_card
        ON usersSearch(userName, search, flashcardName, timeStamp);
    ''')

    # Table to store flashcard study logs with datetimeLastStudy and datetimeNextStudy
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

    # Table for documents
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
    print("Banco de dados e tabelas criados com sucesso!")

if __name__ == "__main__":
    create_empty_db()
