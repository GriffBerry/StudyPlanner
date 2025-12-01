import os
from dataclasses import dataclass

@dataclass
class Config:
    """
    Configuration values loaded from environment variables
    (with sensible defaults for local dev).
    """
    max_hours_per_day: int = int(os.getenv("MAX_HOURS_PER_DAY", "5"))
    planning_horizon_days: int = int(os.getenv("PLANNING_HORIZON_DAYS", "7"))
    db_path: str = os.getenv("DB_PATH", "tasks.db")
    admin_token: str = os.getenv("ADMIN_TOKEN", "")

    @classmethod
    def from_env(cls) -> "Config":
        return cls()
