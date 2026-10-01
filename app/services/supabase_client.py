import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()


@lru_cache
def get_supabase() -> Client:

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url:
        raise RuntimeError("SUPABASE_URL is missing")

    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is missing")

    # Remove accidental whitespace/slashes
    url = url.strip().rstrip("/")

    return create_client(url, key)