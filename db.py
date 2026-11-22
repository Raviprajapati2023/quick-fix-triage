import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# tickets.db lives next to this file, so it works no matter where you start from.
DB_PATH = os.getenv("TICKETS_DB", str(Path(__file__).parent / "tickets.db"))

COLUMNS = [
    "id", "created_at", "channel", "message",
    "category", "urgency", "summary", "customer_name", "address",
    "assigned_to", "alert_sent", "status",
    "ai_category", "ai_urgency",          # what the AI said, kept even after a human fixes it
    "reviewed", "reviewed_by", "reviewed_at",
]


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_dict(row):
    if row is None:
        return None
    d = dict(row)
    d["alert_sent"] = bool(d["alert_sent"])
    d["reviewed"] = bool(d["reviewed"])
    return d


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at    TEXT NOT NULL,
                channel       TEXT,
                message       TEXT NOT NULL,
                category      TEXT,
                urgency       TEXT,
                summary       TEXT,
                customer_name TEXT,
                address       TEXT,
                assigned_to   TEXT,
                alert_sent    INTEGER NOT NULL DEFAULT 0,
                status        TEXT NOT NULL,
                ai_category   TEXT,
                ai_urgency    TEXT,
                reviewed      INTEGER NOT NULL DEFAULT 0,
                reviewed_by   TEXT,
                reviewed_at   TEXT
            )
        """)


def save_ticket(ticket, message):
    """Insert a new ticket and return it (with its id)."""
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO tickets (created_at, channel, message, category, urgency,
                   summary, customer_name, address, assigned_to, alert_sent, status,
                   ai_category, ai_urgency)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                _now(), ticket.get("channel"), message,
                ticket.get("category"), ticket.get("urgency"), ticket.get("summary"),
                ticket.get("customer_name"), ticket.get("address"),
                ticket.get("assigned_to"), int(bool(ticket.get("alert_sent"))),
                ticket.get("status", "ok"),
                ticket.get("category"), ticket.get("urgency"),
            ),
        )
        ticket_id = cur.lastrowid
    return get_ticket(ticket_id)


def get_ticket(ticket_id):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return _to_dict(row)


def list_tickets(status=None, urgency=None, reviewed=None):
    sql = "SELECT * FROM tickets WHERE 1=1"
    params = []
    if status is not None:
        sql += " AND status = ?"
        params.append(status)
    if urgency is not None:
        sql += " AND urgency = ?"
        params.append(urgency)
    if reviewed is not None:
        sql += " AND reviewed = ?"
        params.append(int(reviewed))
    sql += " ORDER BY id DESC"
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_to_dict(r) for r in rows]


def review_ticket(ticket_id, reviewed_by, changes):
    """Apply a human's corrections and mark the ticket reviewed."""
    allowed = {"category", "urgency", "assigned_to", "summary", "customer_name", "address"}
    changes = {k: v for k, v in changes.items() if k in allowed}
    changes.update(reviewed=1, reviewed_by=reviewed_by, reviewed_at=_now(), status="ok")

    sets = ", ".join(f"{k} = ?" for k in changes)
    with _connect() as conn:
        conn.execute(f"UPDATE tickets SET {sets} WHERE id = ?", [*changes.values(), ticket_id])
    return get_ticket(ticket_id)
