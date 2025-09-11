from __future__ import annotations
import sqlite3, json, os, datetime as dt
from typing import Optional, List, Dict, Any

DB_PATH = os.getenv("DB_PATH", "store.db")

def _conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with _conn() as con:
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS orders("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "user_id INTEGER,"
            "username TEXT,"
            "items_json TEXT,"
            "total_rub REAL,"
            "rate REAL,"
            "comment TEXT,"
            "status TEXT,"
            "created_at TEXT)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS settings("
            "key TEXT PRIMARY KEY,"
            "value TEXT)"
        )
        con.commit()

def get_setting(key: str, default: Optional[str]=None) -> Optional[str]:
    with _conn() as con:
        cur = con.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else default

def set_setting(key: str, value: str) -> None:
    with _conn() as con:
        cur = con.cursor()
        cur.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        con.commit()

def save_order(user_id: int, username: str, items: List[Dict[str, Any]], total_rub: float, rate: float, comment: str, status: str="new") -> int:
    with _conn() as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO orders(user_id, username, items_json, total_rub, rate, comment, status, created_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (user_id, username, json.dumps(items, ensure_ascii=False), total_rub, rate, comment, status, dt.datetime.utcnow().isoformat())
        )
        con.commit()
        return cur.lastrowid

def list_orders(limit: int=50) -> List[Dict[str, Any]]:
    with _conn() as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

def export_orders_csv(path: str) -> int:
    import csv, os
    rows = list_orders(10000)
    if not rows:
        return 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","user_id","username","items","total_rub","rate","comment","status","created_at"])
        for r in rows:
            w.writerow([r["id"], r["user_id"], r["username"], r["items_json"], r["total_rub"], r["rate"], r["comment"], r["status"], r["created_at"]])
    return len(rows)
