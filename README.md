# StudyPlanner API

## 1. Executive Summary

StudyPlanner is a small REST API that helps students turn a list of upcoming assignments into a concrete, day-by-day study plan.

Users POST tasks with course, deadline, estimated hours, and difficulty. The system stores tasks in a SQLite database and then uses a simple scheduling algorithm to distribute study sessions across the next few days, respecting a maximum number of hours per day. The API can run both locally and inside a Docker container, making it easy to demo and deploy.

---

## 2. System Overview

**Core idea:**
Given a set of tasks and a limited number of hours per day, generate a feasible short-term plan that tells the student **what to work on each day**.

Main components:

* **HTTP API (Flask)**

  * `GET /health` – health check
  * `GET /tasks` – list saved tasks
  * `POST /tasks` – create a new task
  * `GET /plan` – compute a plan for the next N days
* **Data model (`Task`)** – course, name, deadline, estimated hours, difficulty.
* **Storage (SQLite)** – simple file-based DB via `TaskRepository`.
* **Planner** – greedy scheduling algorithm that allocates study hours day-by-day.

For a visual overview, see the architecture diagram below.

---

## 3. Architecture

![Architecture diagram](assets/arch-diagram.png)

**Flow:**

1. **Client** (curl / Postman / browser) sends HTTP requests to the Flask app.
2. **Flask app (`src/app.py`)** parses requests and:

   * Validates data using the `Task` model (`src/models.py`)
   * Uses `TaskRepository` (`src/storage.py`) to read/write SQLite
   * Calls `build_plan` (`src/planner.py`) to compute the study plan.
3. **SQLite DB** persists tasks on disk (`tasks.db` by default).
4. **Config** (`src/config.py`) controls planning horizon, daily hour limits, and DB path via environment variables or `.env`.

---

## 4. Data Model and Scheduling Logic

### 4.1 Task model

Defined in `src/models.py` using Pydantic:

* `id: int | None`
* `course: str`
* `name: str`
* `deadline: date`
* `est_hours: float` – estimated hours needed
* `difficulty: int` – 1–5 scale

Strings are stripped, and basic validation happens automatically.

### 4.2 Config

Defined in `src/config.py`:

* `MAX_HOURS_PER_DAY` (default: `5`)
* `PLANNING_HORIZON_DAYS` (default: `7`)
* `DB_PATH` (default: `tasks.db`)

These can be controlled through environment variables or an `.env` file.

### 4.3 Planning algorithm (high level)

Implemented in `src/planner.py`:

1. Look at tasks with deadlines **between today and `today + planning_horizon_days`**.

2. For each task, compute a **priority**:

   [
   \text{priority} = \frac{\text{difficulty} \times \text{est_hours}}{\text{days_until_due} + 1}
   ]

3. Sort tasks by **descending** priority.

4. For each task in order, walk through the upcoming days and allocate:

   * up to `2` hours per “session”
   * never exceeding `MAX_HOURS_PER_DAY` on any given day

5. Return a JSON object of the form:

   ```json
   {
     "days": [
       {
         "date": "2025-12-01",
         "total_hours": 3.0,
         "sessions": [
           {
             "task_id": 1,
             "course": "ASTRO",
             "name": "Docker task",
             "hours": 2.0,
             "deadline": "2025-12-05"
           }
         ]
       }
     ]
   }
   ```

If no tasks fall within the planning horizon, the planner returns:

```json
{
  "days": [],
  "message": "No tasks within the planning horizon."
}
```

---

## 5. How to Run the Project (Local)

### 5.1 Prerequisites

* Python 3.11+
* `pip`
* (Optional) `virtualenv` or built-in `venv`

### 5.2 Setup

```bash
git clone <repo-url>        # or copy the folder some other way
cd studyplanner

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 5.3 Configure environment variables

You can use the provided example:

```bash
cp .env.example .env
```

For a simple local run, you can also export them manually:

```bash
export MAX_HOURS_PER_DAY=5
export PLANNING_HORIZON_DAYS=7
export DB_PATH=tasks.db
```

### 5.4 Run the app

```bash
python -m src.app
```

The API will start on `http://localhost:8080`.

---

## 6. How to Run the Project (Docker)

### 6.1 Build the image

From the project root:

```bash
docker build -t studyplanner:latest .
```

### 6.2 Run the container

With default config baked into the image:

```bash
docker run --rm -p 8080:8080 studyplanner:latest
```

Or using the `.env` file:

```bash
docker run --rm -p 8080:8080 --env-file .env studyplanner:latest
```

The API is again available at `http://localhost:8080`.

---

## 7. API Endpoints

### 7.1 `GET /health`

Returns a basic health check.

**Example:**

```bash
curl http://localhost:8080/health
```

**Response:**

```json
{"status": "ok"}
```

---

### 7.2 `POST /tasks`

Create a new task.

**Request:**

```bash
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "course": "ASTRO",
    "name": "LIGO essay",
    "deadline": "2025-12-05",
    "est_hours": 4,
    "difficulty": 4
  }'
```

**Response (example):**

```json
{
  "id": 1,
  "course": "ASTRO",
  "name": "LIGO essay",
  "deadline": "2025-12-05",
  "est_hours": 4.0,
  "difficulty": 4
}
```

---

### 7.3 `GET /tasks`

List all tasks currently stored:

```bash
curl http://localhost:8080/tasks
```

Response is a JSON array of `Task` objects.

---

### 7.4 `GET /plan`

Generate a plan for the next `PLANNING_HORIZON_DAYS` days.

```bash
curl http://localhost:8080/plan
```

Returns the `{"days": [...]} ` structure described in Section 4.3.

---

## 8. Design Decisions and Trade-offs

* **Greedy scheduling** rather than an optimal solver.

  * Pros: simple, explainable, fast, and deterministic.
  * Cons: doesn’t always produce the mathematically optimal plan.
* **SQLite as storage** instead of an in-memory or full external DB.

  * Pros: zero configuration, file-based, good enough for a single-user planner.
  * Cons: not ideal for high-concurrency or multi-user deployments.
* **REST API over CLI/UI**.

  * Pros: easier to test (via `curl`/Postman), can be extended later into a web or mobile frontend.
  * Cons: no fancy GUI yet.
* **Configuration via env variables**.

  * Pros: works well with Docker and `.env` files; flexible per-environment configuration.
  * Cons: slightly more overhead vs hard-coding constants.

---

## 9. Ethics, Security, and Limitations

* **Privacy:**
  The system stores only course names and task descriptions, not grades or sensitive personal data. For a real deployment, we’d want encryption at rest, authentication, and user-specific databases.
* **Scheduling limitations:**
  The algorithm assumes that the student can actually complete the planned sessions and that each hour of work is equal. It doesn’t account for energy levels, overlapping exams, or accessibility concerns.
* **Fairness:**
  The planner currently treats all tasks from the same user uniformly. In a multi-user setting, we would need to consider fairness across users and groups.

---

## 10. Testing

Testing is implemented with **pytest** in the `tests/` folder.

### 10.1 Unit tests for the planner

`tests/test_planner.py`:

* `test_build_plan_allocates_all_hours`

  * Creates a single task and checks that the plan allocates the total estimated hours.
* `test_build_plan_no_tasks_in_horizon`

  * Creates a task with a distant deadline and checks that the planner returns no days and a helpful message.

### 10.2 API smoke tests

`tests/test_api_smoke.py`:

* `test_health_endpoint`

  * Verifies that `GET /health` returns status 200 and `{"status": "ok"}`.
* `test_create_task_and_get_plan`

  * Uses Flask’s test client to:

    * POST a new task
    * Call `GET /plan`
    * Confirm that some hours are allocated in the returned plan.

To run tests:

```bash
pytest
```

All tests currently pass.

---

## 11. Possible Future Improvements

* Add a simple web frontend that visualizes the plan as a calendar.
* Allow updating and deleting tasks via additional endpoints.
* Let users specify preferred study times or blackout dates.
* Experiment with more advanced optimization or fairness constraints.
* Add authentication and per-user task separation.
