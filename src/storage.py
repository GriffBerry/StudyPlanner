import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Iterable, List

from .models import Task

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course TEXT NOT NULL,
    name TEXT NOT NULL,
    deadline TEXT NOT NULL,
    est_hours REAL NOT NULL,
    difficulty INTEGER NOT NULL
);
"""

class TaskRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(SCHEMA)
            conn.commit()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def add_task(self, task: Task) -> Task:
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks (course, name, deadline, est_hours, difficulty)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    task.course,
                    task.name,
                    task.deadline.isoformat(),
                    float(task.est_hours),
                    int(task.difficulty),
                ),
            )
            conn.commit()
            task_id = cur.lastrowid
        return Task(
            id=task_id,
            course=task.course,
            name=task.name,
            deadline=task.deadline,
            est_hours=task.est_hours,
            difficulty=task.difficulty,
        )

    def list_tasks(self) -> List[Task]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT id, course, name, deadline, est_hours, difficulty FROM tasks"
            )
            rows: Iterable[tuple] = cur.fetchall()

        tasks: List[Task] = []
        for row in rows:
            t_id, course, name, deadline_str, est_hours, difficulty = row
            tasks.append(
                Task(
                    id=t_id,
                    course=course,
                    name=name,
                    deadline=date.fromisoformat(deadline_str),
                    est_hours=float(est_hours),
                    difficulty=int(difficulty),
                )
            )
        return tasks

    def clear_all(self) -> None:
        """
        Helper used in tests or debugging.
        """
        with self._conn() as conn:
            conn.execute("DELETE FROM tasks")
            conn.commit()
