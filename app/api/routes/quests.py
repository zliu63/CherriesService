from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.auth_context import CherriesUser, get_user
from app.core.supabase import SupabaseClient, get_supabase_client
from app.core.utils import generate_share_code, get_share_code_expiry, is_share_code_valid
from app.schemas import (
    QuestCreate,
    QuestResponse,
    QuestJoinRequest,
    QuestParticipantResponse,
    ParticipantUserResponse
)

router = APIRouter(prefix="/quests", tags=["Quests"])


async def get_quest_participants(supabase: SupabaseClient, quest_id: str) -> List[ParticipantUserResponse]:
    """Fetch participants for a quest with user metadata (username, avatar)"""
    # Get participants for this quest
    participants_response = supabase.table("quest_participants")\
        .select("user_id, joined_at, total_points")\
        .eq("quest_id", quest_id)\
        .execute()

    if not participants_response.data:
        return []

    participants = []
    for p in participants_response.data:
        # Get user metadata from auth.users
        user_response = supabase.rpc(
            "get_user_metadata",
            {"p_user_id": p["user_id"]}
        ).execute()

        username = None
        avatar = None
        if user_response.data and len(user_response.data) > 0:
            user_meta = user_response.data[0]
            if user_meta.get("raw_user_meta_data"):
                metadata = user_meta["raw_user_meta_data"]
                username = metadata.get("username")
                avatar = metadata.get("avatar")

        participants.append(ParticipantUserResponse(
            user_id=p["user_id"],
            username=username,
            avatar=avatar,
            joined_at=p["joined_at"],
            total_points=p.get("total_points", 0)
        ))

    return participants


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

        # Fetch participants with user info
        quest["participants"] = await get_quest_participants(supabase, quest["id"])

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

        # Add participants to each quest
        result = []
        for quest in quests.data:
            quest["participants"] = await get_quest_participants(supabase, quest["id"])
            result.append(quest)

        return result

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

        quest_data = quest.data
        quest_data["participants"] = await get_quest_participants(supabase, quest_id)

        return quest_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/join", response_model=QuestResponse)
async def join_quest(
    join_data: QuestJoinRequest,
    user: CherriesUser = Depends(get_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Join a quest using share code"""
    try:
        # Find quest by share code with daily tasks
        quest = supabase.table("quests")\
            .select("*, daily_tasks(*)")\
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
        supabase.table("quest_participants").insert({
            "quest_id": quest.data["id"],
            "user_id": user.id
        }).execute()

        # Return full quest with participants
        quest_data = quest.data
        quest_data["participants"] = await get_quest_participants(supabase, quest_data["id"])

        return quest_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
