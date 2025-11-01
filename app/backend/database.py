import os
from supabase import create_client, Client
from functools import lru_cache


@lru_cache
def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Supabase URL and Key must be set in environment variables.")
    return create_client(url, key)