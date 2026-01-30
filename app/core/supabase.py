from supabase import create_client, Client
from fastapi import Header
from app.core.config import settings


def get_supabase(authorization: str = Header(None)) -> Client:
    """
    Dependency for getting Supabase client with user auth context.

    Automatically extracts JWT token from Authorization header and sets it
    on the client, enabling Row Level Security (RLS) policies to work correctly.
    """
    # Create a new client instance for each request
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    # If JWT token exists, set auth context for RLS
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        client.postgrest.auth(token)

    return client


def get_supabase_service() -> Client:
    """Dependency for getting Supabase service client (admin operations)"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
