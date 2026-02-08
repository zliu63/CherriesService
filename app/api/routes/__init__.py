from .auth import router as auth_router
from .quests import router as quests_router
from .checkins import router as checkins_router
from .profile import router as profile_router
from .ws import router as connection_router

__all__ = ["auth_router", "quests_router", "checkins_router", "profile_router", "connection_router"]
