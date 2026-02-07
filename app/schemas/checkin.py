from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime


class CheckInCreate(BaseModel):
    quest_id: str
    daily_task_id: str
    check_in_date: date
    notes: Optional[str] = None


class CheckInResponse(BaseModel):
    id: str
    user_id: str
    quest_id: str
    daily_task_id: str
    check_in_date: date
    count: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CheckInStats(BaseModel):
    quest_id: str
    user_id: str
    total_check_ins: int
    total_points: int
    current_streak: int
    longest_streak: int
