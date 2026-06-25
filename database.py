import pandas as pd
import sqlite3
import hashlib


DB_NAME = "visio_database.db"


def compute_uploaded_file_hash(uploaded_file):
    uploaded_file.seek(0)
    sha256 = hashlib.sha256()
    sha256.update(uploaded_file.getvalue())
    return sha256.hexdigest()


def compute_image_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def image_hash_exists(image_hash):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM images WHERE image_hash=? LIMIT 1", (image_hash,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def get_db_as_df():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM images", conn)
    conn.close()
    return df


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS images (
                                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                            image_hash TEXT UNIQUE,
                                                            filename TEXT,
                                                            filepath TEXT,
                                                            upload_date TEXT,
                                                            manual_annotation TEXT,
                                                            ai_annotation TEXT,
                                                            ai_confidence REAL,
                                                            file_size INTEGER,
                                                            width INTEGER,
                                                            height INTEGER,
                                                            avg_r INTEGER,
                                                            avg_g INTEGER,
                                                            avg_b INTEGER)""")
    conn.commit()
    conn.close()


def insert_image(data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO images(filename, image_hash, filepath, upload_date, manual_annotation, ai_annotation, ai_confidence, file_size, width, height, avg_r, avg_g, avg_b) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", data)
    conn.commit()
    conn.close()


def update_manual_annotation(m_annotation, hash):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE images SET manual_annotation=? WHERE image_hash=?", (m_annotation, hash))
    conn.commit()
    conn.close()
