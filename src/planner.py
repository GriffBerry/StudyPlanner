from datetime import date, timedelta
from typing import Any, Dict, List

from .config import Config
from .models import Task

def build_plan(tasks: List[Task], config: Config | None = None) -> Dict[str, Any]:
    """
    Build a study plan for the next config.planning_horizon_days days.

    Strategy:
      * Filter tasks with deadlines in the horizon.
      * Compute a priority score: (difficulty * est_hours) / days_until_due.
      * Sort by descending priority.
      * Greedily assign hours, capped by max_hours_per_day and per-slot chunk.
    """
    cfg = config or Config.from_env()
    today = date.today()

    horizon_dates: List[date] = [
        today + timedelta(days=i) for i in range(cfg.planning_horizon_days)
    ]

    # Filter tasks that are still relevant within the horizon
    eligible_tasks: List[Task] = [
        t for t in tasks
        if t.deadline >= today and t.deadline <= horizon_dates[-1]
    ]

    if not eligible_tasks:
        return {
            "days": [],
            "message": "No tasks within the planning horizon.",
        }

    def priority(task: Task) -> float:
        days_until_due = max((task.deadline - today).days, 0) + 1
        # Higher difficulty and more hours => higher priority,
        # but urgency increases as days_until_due decreases.
        return (task.difficulty * task.est_hours) / float(days_until_due)

    eligible_tasks.sort(key=priority, reverse=True)

    # Per-day capacity and per-task remaining hours
    day_capacity: Dict[date, float] = {d: float(cfg.max_hours_per_day) for d in horizon_dates}
    remaining: Dict[int, float] = {
        int(t.id) if t.id is not None else idx: float(t.est_hours)
        for idx, t in enumerate(eligible_tasks, start=1)
    }

    # Map actual IDs used in "remaining" back to tasks
    id_map: Dict[int, Task] = {}
    for idx, t in enumerate(eligible_tasks, start=1):
        key = int(t.id) if t.id is not None else idx
        id_map[key] = t

    schedule: Dict[str, List[Dict[str, Any]]] = {
        d.isoformat(): [] for d in horizon_dates
    }

    # Greedy allocation: for each task, walk through days
    for key, task in id_map.items():
        for day in horizon_dates:
            if remaining[key] <= 0:
                break
            if day_capacity[day] <= 0:
                continue

            # Hours to allocate in this "session"
            chunk = min(2.0, day_capacity[day], remaining[key])
            if chunk <= 0:
                continue

            schedule[day.isoformat()].append(
                {
                    "task_id": task.id,
                    "course": task.course,
                    "name": task.name,
                    "hours": chunk,
                    "deadline": task.deadline.isoformat(),
                }
            )

            remaining[key] -= chunk
            day_capacity[day] -= chunk

    days_out: List[Dict[str, Any]] = []
    for d in horizon_dates:
        day_str = d.isoformat()
        assigned_hours = sum(sess["hours"] for sess in schedule[day_str])
        days_out.append(
            {
                "date": day_str,
                "total_hours": assigned_hours,
                "sessions": schedule[day_str],
            }
        )

    return {"days": days_out}
