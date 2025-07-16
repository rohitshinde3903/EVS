import sqlite3

# Path to your SQLite database
DATABASE_PATH = 'database.db'

# Connect to the SQLite database
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Create Voters table with an email column
cursor.execute('''
CREATE TABLE IF NOT EXISTS voters (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    class TEXT NOT NULL,
    email TEXT NOT NULL,
    voted INTEGER DEFAULT 0
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS voters_auth (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    password TEXT,
    au_otp TEXT,
    au_status TEXT,
);
''')

# Create Candidates table with image column
cursor.execute('''
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    class TEXT NOT NULL,
    position TEXT NOT NULL,
    votes INTEGER DEFAULT 0,
    image TEXT
);
''')

# Insert sample data into the Voters table
cursor.execute("INSERT INTO voters (id, name, class, email, voted) VALUES (11, 'John Doe', 'Class 10', 'rohitshinde3903@gmail.com', 0);"),
cursor.execute("INSERT INTO voters (id, name, class, email, voted) VALUES (22, 'Jane Smith', 'Class 11', 'jane.smith@example.com', 0);")
cursor.execute("INSERT INTO voters (id, name, class, email, voted) VALUES (33, 'Robert Brown', 'Class 12', 'robert.brown@example.com', 0);")

# Insert sample data into the Candidates table
cursor.execute("INSERT INTO candidates (name, class, position, votes, image) VALUES ('Alice Johnson', 'Class 10', 'President', 0, 'path/to/image1.jpg');")
cursor.execute("INSERT INTO candidates (name, class, position, votes, image) VALUES ('David Wilson', 'Class 11', 'Vice President', 0, 'path/to/image2.jpg');")
cursor.execute("INSERT INTO candidates (name, class, position, votes, image) VALUES ('Emily Davis', 'Class 12', 'Treasurer', 0, 'path/to/image3.jpg');")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database setup completed successfully.")
