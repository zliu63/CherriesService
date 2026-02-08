from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
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

    # Authenticate via JWT
    supabase = get_supabase_client()
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            await websocket.close(code=4001, reason="Invalid token")
            return
        user = user_response.user
    except Exception:
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

    manager.connect(quest_id, user.id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(quest_id, user.id)
