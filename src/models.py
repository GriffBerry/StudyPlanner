from datetime import date
from pydantic import BaseModel, Field, validator

class Task(BaseModel):
    """
    A study task entered by a user.
    """
    id: int | None = None
    course: str = Field(min_length=1)
    name: str = Field(min_length=1)
    deadline: date
    est_hours: float = Field(gt=0)
    difficulty: int = Field(ge=1, le=5)

    @validator("course", "name")
    def strip_strings(cls, v: str) -> str:
        return v.strip()
