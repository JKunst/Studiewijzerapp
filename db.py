import sqlite3
import pandas as pd
import json

DB_PATH = "studiewijzers.db"


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS studiewijzers (
                vak TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)
        conn.commit()


def save_studiewijzer(vak: str, df: pd.DataFrame):
    data_json = df.to_json(orient="split")
    with get_connection() as conn:
        conn.execute(
            "REPLACE INTO studiewijzers (vak, data) VALUES (?, ?)",
            (vak, data_json)
        )
        conn.commit()


def load_all_studiewijzers() -> dict:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT vak, data FROM studiewijzers"
        ).fetchall()

    result = {}
    for vak, data_json in rows:
        result[vak] = pd.read_json(data_json, orient="split")
    return result


def delete_studiewijzer(vak: str):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM studiewijzers WHERE vak = ?",
            (vak,)
        )
        conn.commit()
