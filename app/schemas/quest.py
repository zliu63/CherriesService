from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import date, datetime


class ParticipantUserResponse(BaseModel):
    """Participant information for display in quest cards"""
    user_id: str
    username: Optional[str] = None
    avatar: Optional[dict] = None  # {"type": "emoji", "value": "🐶"}
    joined_at: datetime
    total_points: int = 0

    model_config = ConfigDict(from_attributes=True)


class DailyTaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    points: int = 10


class DailyTaskCreate(DailyTaskBase):
    pass


class DailyTaskResponse(DailyTaskBase):
    id: str
    quest_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date


class QuestCreate(QuestBase):
    daily_tasks: List[DailyTaskCreate] = []


class QuestResponse(QuestBase):
    id: str
    creator_id: str
    share_code: str
    share_code_expires_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    daily_tasks: List[DailyTaskResponse] = []
    participants: List[ParticipantUserResponse] = []

    model_config = ConfigDict(from_attributes=True)


class QuestJoinRequest(BaseModel):
    share_code: str


class QuestParticipantResponse(BaseModel):
    quest_id: str
    user_id: str
    joined_at: datetime
    total_points: int = 0

    model_config = ConfigDict(from_attributes=True)
