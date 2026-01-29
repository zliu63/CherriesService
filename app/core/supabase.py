from supabase import create_client, Client
from app.core.config import settings


class SupabaseClient:
    """Supabase client singleton"""

    _client: Client = None
    _service_client: Client = None

    @classmethod
    def get_client(cls) -> Client:
        """Get Supabase client with anon key (for user operations)"""
        if cls._client is None:
            cls._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return cls._client

    @classmethod
    def get_service_client(cls) -> Client:
        """Get Supabase client with service role key (for admin operations)"""
        if cls._service_client is None:
            cls._service_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return cls._service_client


def get_supabase() -> Client:
    """Dependency for getting Supabase client"""
    return SupabaseClient.get_client()


def get_supabase_service() -> Client:
    """Dependency for getting Supabase service client"""
    return SupabaseClient.get_service_client()
