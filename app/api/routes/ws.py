from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from app.core.logging import logger
from app.core.supabase import get_supabase_client
from app.core.connection_manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/quests/{quest_id}")
async def quest_websocket(
    websocket: WebSocket,
    quest_id: str,
    token: str = Query(...),
):
    await websocket.accept()
    logger.debug("WebSocket connection attempt: quest_id=%s", quest_id)

    # Authenticate via JWT
    supabase = get_supabase_client()
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            logger.warning("WebSocket auth failed: invalid token, quest_id=%s", quest_id)
            await websocket.close(code=4001, reason="Invalid token")
            return
        user = user_response.user
    except Exception:
        logger.warning("WebSocket auth error: quest_id=%s", quest_id)
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Verify user is a participant
    participant = supabase.table("quest_participants")\
        .select("user_id")\
        .eq("quest_id", quest_id)\
        .eq("user_id", user.id)\
        .execute()
    if not participant.data:
        await websocket.close(code=4003, reason="Not a participant")
        return

    logger.info("WebSocket connected: user_id=%s, quest_id=%s", user.id, quest_id)
    manager.connect(quest_id, user.id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: user_id=%s, quest_id=%s", user.id, quest_id)
        manager.disconnect(quest_id, user.id)
