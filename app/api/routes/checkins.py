from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import date

from app.core.auth_context import CherriesUser, get_user
from app.core.supabase import SupabaseClient, get_supabase_client
from app.core.connection_manager import manager as connection_manager
from app.schemas import CheckInCreate, CheckInResponse, CheckInStats

router = APIRouter(prefix="/checkins", tags=["Check-ins"])


@router.post("/increment", response_model=CheckInResponse)
async def increment_checkin(
    checkin_data: CheckInCreate,
    user: CherriesUser = Depends(get_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Increment check-in count. Creates new record if not exists, otherwise increments count."""
    try:
        # Verify user is a participant of the quest
        participant = supabase.table("quest_participants")\
            .select("*")\
            .eq("quest_id", checkin_data.quest_id)\
            .eq("user_id", user.id)\
            .execute()
        if not participant.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a participant of this quest"
            )

        # Get task points
        task = supabase.table("daily_tasks")\
            .select("points")\
            .eq("id", checkin_data.daily_task_id)\
            .single()\
            .execute()

        points_to_add = task.data["points"]

        # Check if check-in already exists for this user/task/date
        existing = supabase.table("check_ins")\
            .select("*")\
            .eq("user_id", user.id)\
            .eq("daily_task_id", checkin_data.daily_task_id)\
            .eq("check_in_date", checkin_data.check_in_date.isoformat())\
            .execute()

        if existing.data:
            # Increment existing check-in count
            current_count = existing.data[0]["count"]
            checkin = supabase.table("check_ins")\
                .update({"count": current_count + 1})\
                .eq("id", existing.data[0]["id"])\
                .execute()
        else:
            # Create new check-in with count=1
            checkin = supabase.table("check_ins").insert({
                "user_id": user.id,
                "quest_id": checkin_data.quest_id,
                "daily_task_id": checkin_data.daily_task_id,
                "check_in_date": checkin_data.check_in_date.isoformat(),
                "count": 1,
                "notes": checkin_data.notes
            }).execute()

        # Update participant's total points
        current_points = participant.data[0]["total_points"]
        supabase.table("quest_participants")\
            .update({"total_points": current_points + points_to_add})\
            .eq("quest_id", checkin_data.quest_id)\
            .eq("user_id", user.id)\
            .execute()

        await connection_manager.broadcast(
            checkin_data.quest_id,
            {"type": "scoreboard_update", "quest_id": checkin_data.quest_id},
        )

        return checkin.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/decrement", response_model=Optional[CheckInResponse])
async def decrement_checkin(
    checkin_data: CheckInCreate,
    user: CherriesUser = Depends(get_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Decrement check-in count. If count becomes 0, deletes the record. Returns null if deleted."""
    try:
        # Verify user is a participant of the quest
        participant = supabase.table("quest_participants")\
            .select("*")\
            .eq("quest_id", checkin_data.quest_id)\
            .eq("user_id", user.id)\
            .execute()
        if not participant.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a participant of this quest"
            )

        # Get task points
        task = supabase.table("daily_tasks")\
            .select("points")\
            .eq("id", checkin_data.daily_task_id)\
            .single()\
            .execute()

        points_to_subtract = task.data["points"]

        # Check if check-in exists for this user/task/date
        existing = supabase.table("check_ins")\
            .select("*")\
            .eq("user_id", user.id)\
            .eq("daily_task_id", checkin_data.daily_task_id)\
            .eq("check_in_date", checkin_data.check_in_date.isoformat())\
            .execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Check-in not found"
            )

        current_count = existing.data[0]["count"]
        checkin_id = existing.data[0]["id"]

        if current_count > 1:
            # Decrement count
            checkin = supabase.table("check_ins")\
                .update({"count": current_count - 1})\
                .eq("id", checkin_id)\
                .execute()
            result = checkin.data[0]
        else:
            # Delete the record when count would become 0
            supabase.table("check_ins")\
                .delete()\
                .eq("id", checkin_id)\
                .execute()
            result = None

        # Subtract points from participant's total
        current_points = participant.data[0]["total_points"]
        new_points = max(0, current_points - points_to_subtract)
        supabase.table("quest_participants")\
            .update({"total_points": new_points})\
            .eq("quest_id", checkin_data.quest_id)\
            .eq("user_id", user.id)\
            .execute()

        await connection_manager.broadcast(
            checkin_data.quest_id,
            {"type": "scoreboard_update", "quest_id": checkin_data.quest_id},
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/quest/{quest_id}", response_model=List[CheckInResponse])
async def get_quest_checkins(
    quest_id: str,
    date: Optional[date] = None,
    user: CherriesUser = Depends(get_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Get check-ins for a quest. If date is provided, returns check-ins for that month only."""
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

        # Build query
        query = supabase.table("check_ins")\
            .select("*")\
            .eq("quest_id", quest_id)\
            .eq("user_id", user.id)

        # Filter by month if date is provided
        if date:
            first_day = date.replace(day=1)
            if date.month == 12:
                last_day = date.replace(year=date.year + 1, month=1, day=1)
            else:
                last_day = date.replace(month=date.month + 1, day=1)

            query = query.gte("check_in_date", first_day.isoformat())\
                         .lt("check_in_date", last_day.isoformat())

        checkins = query.order("check_in_date", desc=True).execute()

        return checkins.data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/stats/{quest_id}", response_model=CheckInStats)
async def get_checkin_stats(
    quest_id: str,
    user: CherriesUser = Depends(get_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Get check-in statistics for a quest"""
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

        # Get all check-ins
        checkins = supabase.table("check_ins")\
            .select("*")\
            .eq("quest_id", quest_id)\
            .eq("user_id", user.id)\
            .order("check_in_date", desc=False)\
            .execute()

        total_check_ins = sum(c.get("count", 1) for c in checkins.data)
        total_points = participant.data[0]["total_points"]

        # Calculate streaks
        current_streak = 0
        longest_streak = 0
        temp_streak = 0

        if checkins.data:
            from datetime import datetime, timedelta
            today = date.today()
            last_date = None

            for checkin in checkins.data:
                checkin_date = datetime.fromisoformat(checkin["check_in_date"]).date()

                if last_date is None:
                    temp_streak = 1
                elif (checkin_date - last_date).days == 1:
                    temp_streak += 1
                else:
                    temp_streak = 1

                longest_streak = max(longest_streak, temp_streak)
                last_date = checkin_date

            # Check current streak
            if last_date == today or last_date == today - timedelta(days=1):
                current_streak = temp_streak

        return CheckInStats(
            quest_id=quest_id,
            user_id=user.id,
            total_check_ins=total_check_ins,
            total_points=total_points,
            current_streak=current_streak,
            longest_streak=longest_streak
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
