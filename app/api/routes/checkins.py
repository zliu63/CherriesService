from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import date
from app.core.utils import AuthContext, get_auth_context
from app.schemas import CheckInCreate, CheckInResponse, CheckInStats

router = APIRouter(prefix="/checkins", tags=["Check-ins"])


@router.post("", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def create_checkin(
    checkin_data: CheckInCreate,
    auth: AuthContext = Depends(get_auth_context)
):
    """Create a new check-in"""
    try:
        # Verify user is a participant of the quest
        participant = auth.supabase.table("quest_participants")\
            .select("*")\
            .eq("quest_id", checkin_data.quest_id)\
            .eq("user_id", auth.user_id)\
            .execute()

        if not participant.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a participant of this quest"
            )

        # Check if already checked in for this task today
        existing = auth.supabase.table("check_ins")\
            .select("*")\
            .eq("user_id", auth.user_id)\
            .eq("daily_task_id", checkin_data.daily_task_id)\
            .eq("check_in_date", checkin_data.check_in_date.isoformat())\
            .execute()

        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked in for this task today"
            )

        # Get task points
        task = auth.supabase.table("daily_tasks")\
            .select("points")\
            .eq("id", checkin_data.daily_task_id)\
            .single()\
            .execute()

        points_earned = task.data["points"]

        # Create check-in
        checkin = auth.supabase.table("check_ins").insert({
            "user_id": auth.user_id,
            "quest_id": checkin_data.quest_id,
            "daily_task_id": checkin_data.daily_task_id,
            "check_in_date": checkin_data.check_in_date.isoformat(),
            "points_earned": points_earned,
            "notes": checkin_data.notes
        }).execute()

        # Update participant's total points
        current_points = participant.data[0]["total_points"]
        auth.supabase.table("quest_participants")\
            .update({"total_points": current_points + points_earned})\
            .eq("quest_id", checkin_data.quest_id)\
            .eq("user_id", auth.user_id)\
            .execute()

        return checkin.data[0]

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
    auth: AuthContext = Depends(get_auth_context)
):
    """Get all check-ins for a quest"""
    try:
        # Verify user is a participant
        participant = auth.supabase.table("quest_participants")\
            .select("*")\
            .eq("quest_id", quest_id)\
            .eq("user_id", auth.user_id)\
            .execute()

        if not participant.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a participant of this quest"
            )

        # Get check-ins
        checkins = auth.supabase.table("check_ins")\
            .select("*")\
            .eq("quest_id", quest_id)\
            .eq("user_id", auth.user_id)\
            .order("check_in_date", desc=True)\
            .execute()

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
    auth: AuthContext = Depends(get_auth_context)
):
    """Get check-in statistics for a quest"""
    try:
        # Verify user is a participant
        participant = auth.supabase.table("quest_participants")\
            .select("*")\
            .eq("quest_id", quest_id)\
            .eq("user_id", auth.user_id)\
            .execute()

        if not participant.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a participant of this quest"
            )

        # Get all check-ins
        checkins = auth.supabase.table("check_ins")\
            .select("*")\
            .eq("quest_id", quest_id)\
            .eq("user_id", auth.user_id)\
            .order("check_in_date", desc=False)\
            .execute()

        total_check_ins = len(checkins.data)
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
            user_id=auth.user_id,
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
