import sqlite3
from datetime import datetime
from logger import get_logger

logger = get_logger(__name__)

DB_PATH = "vector.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                notes TEXT,
                priority INTEGER,
                target_date TEXT,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)
    logger.info("Task database initialized.")


# --- CRUD ---

def create_task(title: str, notes: str = None, priority: int = None, target_date: str = None) -> dict:
    created_at = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, notes, priority, target_date, created_at) VALUES (?, ?, ?, ?, ?)",
            (title, notes, priority, target_date, created_at)
        )
        task_id = cursor.lastrowid
    logger.info(f"Task created: [{task_id}] {title}")
    return get_task(task_id)


def get_task(task_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _row_to_dict(row) if row else None


def get_open_tasks() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE completed = 0 ORDER BY created_at ASC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]

def get_formatted_open_tasks() -> str:
    tasks = get_open_tasks()
    if not tasks:
        return "_No open tasks._"
    lines = [f"- [{t['id']}] {t['title']} (priority: {t['priority'] or 'null'}, target_date: {t['target_date'] or 'null'})" for t in tasks]
    return "\n".join(lines)

def get_completed_tasks() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE completed = 1 ORDER BY completed_at DESC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def edit_task(task_id: int, title: str = None, notes: str = None, priority: int = None, target_date: str = None) -> dict:
    task = get_task(task_id)
    if not task:
        logger.error(f"Task {task_id} not found.")
        return None
    new_title = title if title is not None else task["title"]
    new_notes = notes if notes is not None else task["notes"]
    new_priority = priority if priority is not None else task["priority"]
    new_target_date = target_date if target_date is not None else task["target_date"]
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET title = ?, notes = ?, priority = ?, target_date = ? WHERE id = ?",
            (new_title, new_notes, new_priority, new_target_date, task_id)
        )
    logger.info(f"Task updated: [{task_id}]")
    return get_task(task_id)


def complete_task(task_id: int) -> dict:
    completed_at = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET completed = 1, completed_at = ? WHERE id = ?",
            (completed_at, task_id)
        )
    logger.info(f"Task completed: [{task_id}]")
    return get_task(task_id)


def delete_task(task_id: int) -> bool:
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    logger.info(f"Task deleted: [{task_id}]")
    return True


# --- Helpers ---

def _row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "notes": row[2],
        "priority": row[3],
        "target_date": row[4],
        "completed": bool(row[5]),
        "created_at": row[6],
        "completed_at": row[7]
    }