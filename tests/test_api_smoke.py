from datetime import date, timedelta
from pathlib import Path

from src.app import create_app
from src.config import Config


def _test_config(tmp_path: Path) -> Config:
    return Config(
        max_hours_per_day=5,
        planning_horizon_days=7,
        db_path=str(tmp_path / "test_tasks.db"),
    )


def test_health_endpoint(tmp_path):
    cfg = _test_config(tmp_path)
    app = create_app(cfg)
    client = app.test_client()

    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_create_task_and_get_plan(tmp_path):
    cfg = _test_config(tmp_path)
    app = create_app(cfg)
    client = app.test_client()

    deadline = date.today() + timedelta(days=2)

    resp = client.post(
        "/tasks",
        json={
            "course": "ASTRO",
            "name": "Study for exam",
            "deadline": deadline.isoformat(),
            "est_hours": 3,
            "difficulty": 4,
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["id"] is not None

    plan_resp = client.get("/plan")
    assert plan_resp.status_code == 200
    plan = plan_resp.get_json()
    assert "days" in plan
    assert any(day["total_hours"] > 0 for day in plan["days"])
