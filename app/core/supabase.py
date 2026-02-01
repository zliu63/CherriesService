from supabase import create_client, Client as _SupabaseClient

from app.core.config import settings

# Type alias for Supabase Client - import this instead of supabase.Client
SupabaseClient = _SupabaseClient

# Service client (bypasses RLS) - created at module load, thread-safe
_service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def get_supabase_client() -> SupabaseClient:
    """Get Supabase service client (bypasses RLS)."""
    return _service_client

def get_anon_client() -> SupabaseClient:
    """Get Supabase user client (enabled RLS)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)