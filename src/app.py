from datetime import date
from typing import Any, Dict

from flask import Flask, jsonify, request

from .config import Config
from .models import Task
from .planner import build_plan
from .storage import TaskRepository

def create_app(config: Config | None = None) -> Flask:
    cfg = config or Config.from_env()
    repo = TaskRepository(cfg.db_path)

    app = Flask(__name__)
    app.config["APP_CONFIG"] = cfg
    app.config["TASK_REPO"] = repo

    @app.route("/health", methods=["GET"])
    def health() -> Any:
        return jsonify({"status": "ok"}), 200

    @app.route("/tasks", methods=["GET"])
    def list_tasks() -> Any:
        tasks = repo.list_tasks()
        return jsonify([t.dict() for t in tasks]), 200

    @app.route("/tasks", methods=["POST"])
    def create_task() -> Any:
        payload: Dict[str, Any] | None = request.get_json()
        if payload is None:
            return jsonify({"error": "JSON body required"}), 400

        try:
            deadline_str = payload["deadline"]
            est_hours = float(payload["est_hours"])
            difficulty = int(payload["difficulty"])
            course = str(payload.get("course", "")).strip()
            name = str(payload.get("name", "")).strip()
            deadline = date.fromisoformat(deadline_str)
        except KeyError as e:
            return jsonify({"error": f"Missing field: {e}"}), 400
        except ValueError as e:
            return jsonify({"error": f"Invalid field value: {e}"}), 400

        try:
            task_model = Task(
                course=course,
                name=name,
                deadline=deadline,
                est_hours=est_hours,
                difficulty=difficulty,
            )
        except Exception as e:  # pydantic validation error
            return jsonify({"error": f"Validation error: {e}"}), 400

        created = repo.add_task(task_model)
        app.logger.info("Created task %s", created.id)
        return jsonify(created.dict()), 201

    @app.route("/plan", methods=["GET"])
    def get_plan() -> Any:
        tasks = repo.list_tasks()
        if not tasks:
            return jsonify({"message": "No tasks available"}), 200

        cfg_local = app.config["APP_CONFIG"]
        plan = build_plan(tasks, config=cfg_local)
        app.logger.info("Generated plan for %d tasks", len(tasks))
        return jsonify(plan), 200

    return app

# Entry point for "python -m src.app"
if __name__ == "__main__":
    cfg = Config.from_env()
    app = create_app(cfg)
    app.run(host="0.0.0.0", port=8080, debug=True)
