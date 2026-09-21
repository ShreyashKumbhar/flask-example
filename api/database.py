import hashlib
import os
import time

import psycopg2


def _db_params():
    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
        "dbname": os.environ.get("POSTGRES_DB", "flask"),
        "user": os.environ.get("POSTGRES_USER", "flask"),
        "password": os.environ.get("POSTGRES_PASSWORD", "flask"),
    }


def get_conn():
    return psycopg2.connect(**_db_params())


def wait_for_db(attempts=30, delay=1):
    last_error = None
    for _ in range(attempts):
        try:
            conn = get_conn()
            conn.close()
            return
        except psycopg2.OperationalError as exc:
            last_error = exc
            time.sleep(delay)
    raise RuntimeError("Could not connect to Postgres") from last_error


def init_schema():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    pw TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS notes (
                    user_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    note TEXT,
                    note_id TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS images (
                    uid TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    name TEXT,
                    timestamp TEXT
                );
                """
            )
            cur.execute("SELECT COUNT(*) FROM users;")
            if cur.fetchone()[0] == 0:
                cur.executemany(
                    "INSERT INTO users (id, pw) VALUES (%s, %s);",
                    [
                        ("ADMIN", hashlib.sha256(b"admin").hexdigest()),
                        ("TEST", hashlib.sha256(b"123456").hexdigest()),
                    ],
                )
        conn.commit()
    finally:
        conn.close()


def list_users():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users ORDER BY id;")
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def verify(user_id, pw):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pw FROM users WHERE id = %s;", (user_id,))
            row = cur.fetchone()
            if row is None:
                return False
            return row[0] == hashlib.sha256(pw.encode()).hexdigest()
    finally:
        conn.close()


def delete_user_from_db(user_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
            cur.execute("DELETE FROM notes WHERE user_id = %s;", (user_id,))
            cur.execute("DELETE FROM images WHERE owner = %s;", (user_id,))
        conn.commit()
    finally:
        conn.close()


def add_user(user_id, pw):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (id, pw) VALUES (%s, %s);",
                (user_id.upper(), hashlib.sha256(pw.encode()).hexdigest()),
            )
        conn.commit()
    finally:
        conn.close()


def read_note_from_db(user_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT note_id, timestamp, note FROM notes WHERE user_id = %s;",
                (user_id.upper(),),
            )
            return cur.fetchall()
    finally:
        conn.close()


def match_user_id_with_note_id(note_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM notes WHERE note_id = %s;", (note_id,))
            row = cur.fetchone()
            return None if row is None else row[0]
    finally:
        conn.close()


def write_note_into_db(user_id, note_to_write):
    import datetime

    conn = get_conn()
    try:
        current_timestamp = str(datetime.datetime.now())
        note_id = hashlib.sha1((user_id.upper() + current_timestamp).encode()).hexdigest()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO notes (user_id, timestamp, note, note_id) VALUES (%s, %s, %s, %s);",
                (user_id.upper(), current_timestamp, note_to_write, note_id),
            )
        conn.commit()
        return note_id
    finally:
        conn.close()


def delete_note_from_db(note_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notes WHERE note_id = %s;", (note_id,))
        conn.commit()
    finally:
        conn.close()


def image_upload_record(uid, owner, image_name, timestamp):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO images (uid, owner, name, timestamp) VALUES (%s, %s, %s, %s);",
                (uid, owner, image_name, timestamp),
            )
        conn.commit()
    finally:
        conn.close()


def list_images_for_user(owner):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT uid, timestamp, name FROM images WHERE owner = %s;",
                (owner,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def match_user_id_with_image_uid(image_uid):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT owner FROM images WHERE uid = %s;", (image_uid,))
            row = cur.fetchone()
            return None if row is None else row[0]
    finally:
        conn.close()


def delete_image_from_db(image_uid):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM images WHERE uid = %s;", (image_uid,))
        conn.commit()
    finally:
        conn.close()
