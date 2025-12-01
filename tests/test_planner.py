from datetime import date, timedelta

from src.config import Config
from src.models import Task
from src.planner import build_plan


def test_build_plan_allocates_all_hours():
    today = date.today()
    task = Task(
        id=1,
        course="ASTRO",
        name="Write LIGO essay",
        deadline=today + timedelta(days=3),
        est_hours=4,
        difficulty=4,
    )

    cfg = Config(
        max_hours_per_day=5,
        planning_horizon_days=7,
        db_path=":memory:",
    )

    plan = build_plan([task], config=cfg)
    assert "days" in plan
    days = plan["days"]
    total_hours = sum(day["total_hours"] for day in days)
    # We expect roughly 4 hours allocated (float math tolerance)
    assert abs(total_hours - 4.0) < 1e-6


def test_build_plan_no_tasks_in_horizon():
    today = date.today()
    # Deadline too far in future
    task = Task(
        id=1,
        course="MATH",
        name="Final project",
        deadline=today + timedelta(days=30),
        est_hours=10,
        difficulty=3,
    )

    cfg = Config(
        max_hours_per_day=5,
        planning_horizon_days=7,
        db_path=":memory:",
    )

    plan = build_plan([task], config=cfg)
    assert plan["days"] == []
    assert "No tasks within the planning horizon" in plan["message"]
