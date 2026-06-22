import sqlite3

DB_NAME = "visio_database.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS images (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filepath TEXT, upload_date TEXT, annotation TEXT, file_size REAL, width INTEGER, height INTEGER, avg_r REAL, avg_g REAL, avg_b REAL)")
    conn.commit()
    conn.close()


def insert_image(data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO images(filename, filepath, upload_date, annotation, file_size, width, height, avg_r, avg_g, avg_b) VALUES(?,?,?,?,?,?,?,?,?,?)", data)
    conn.commit()
    conn.close()
