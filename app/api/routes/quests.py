from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.auth_context import CherriesUser, get_user
from app.core.supabase import SupabaseClient, get_supabase_client
from app.core.utils import generate_share_code, get_share_code_expiry, is_share_code_valid
from app.schemas import (
    QuestCreate,
    QuestResponse,
    QuestJoinRequest,
    QuestParticipantResponse
)

router = APIRouter(prefix="/quests", tags=["Quests"])


@router.post("", response_model=QuestResponse, status_code=status.HTTP_201_CREATED)
async def create_quest(
    quest_data: QuestCreate,
    user: CherriesUser = Depends(get_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Create a new quest"""
    try:
        # Generate unique share code
        share_code = generate_share_code()
        share_code_expires_at = get_share_code_expiry()
        # Create quest
        quest_response = supabase.table("quests").insert({
            "name": quest_data.name,
            "description": quest_data.description,
            "start_date": quest_data.start_date.isoformat(),
            "end_date": quest_data.end_date.isoformat(),
            "creator_id": user.id,
            "share_code": share_code,
            "share_code_expires_at": share_code_expires_at.isoformat()
        }).execute()

        quest = quest_response.data[0]

        # Create daily tasks
        daily_tasks = []
        if quest_data.daily_tasks:
            for task in quest_data.daily_tasks:
                task_response = supabase.table("daily_tasks").insert({
                    "quest_id": quest["id"],
                    "title": task.title,
                    "description": task.description,
                    "points": task.points
                }).execute()
                daily_tasks.append(task_response.data[0])

        # Add creator as participant
        supabase.table("quest_participants").insert({
            "quest_id": quest["id"],
            "user_id": user.id
        }).execute()

        quest["daily_tasks"] = daily_tasks
        return quest

    except Exception as e:
        import traceback
        print(f"Error : {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[QuestResponse])
async def get_user_quests(
    user: CherriesUser = Depends(get_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Get all quests for the current user"""
    try:
        # Get quest IDs for user
        participants = supabase.table("quest_participants")\
            .select("quest_id")\
            .eq("user_id", user.id)\
            .execute()

        quest_ids = [p["quest_id"] for p in participants.data]

        if not quest_ids:
            return []

        # Get quests with daily tasks
        quests = supabase.table("quests")\
            .select("*, daily_tasks(*)")\
            .in_("id", quest_ids)\
            .execute()

        return quests.data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{quest_id}", response_model=QuestResponse)
async def get_quest(
    quest_id: str,
    user: CherriesUser = Depends(get_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Get a specific quest"""
    try:
        # Verify user is a participant
        participant = supabase.table("quest_participants")\
            .select("*")\
            .eq("quest_id", quest_id)\
            .eq("user_id", user.id)\
            .execute()

        if not participant.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a participant of this quest"
            )

        # Get quest with daily tasks
        quest = supabase.table("quests")\
            .select("*, daily_tasks(*)")\
            .eq("id", quest_id)\
            .single()\
            .execute()

        return quest.data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/join", response_model=QuestParticipantResponse)
async def join_quest(
    join_data: QuestJoinRequest,
    user: CherriesUser = Depends(get_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Join a quest using share code"""
    try:
        # Find quest by share code
        quest = supabase.table("quests")\
            .select("*")\
            .eq("share_code", join_data.share_code)\
            .single()\
            .execute()

        if not quest.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid share code"
            )

        # Check if share code is expired
        from datetime import datetime
        expires_at = datetime.fromisoformat(quest.data["share_code_expires_at"])
        if not is_share_code_valid(expires_at):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Share code has expired"
            )

        # Check if user is already a participant
        existing = supabase.table("quest_participants")\
            .select("*")\
            .eq("quest_id", quest.data["id"])\
            .eq("user_id", user.id)\
            .execute()

        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already a participant of this quest"
            )

        # Add user as participant
        participant = supabase.table("quest_participants").insert({
            "quest_id": quest.data["id"],
            "user_id": user.id
        }).execute()

        return participant.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
