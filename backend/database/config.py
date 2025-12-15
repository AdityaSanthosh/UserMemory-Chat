import os

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Initialize Supabase client
db = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_db():
    """Dependency to get Supabase client"""
    return db


async def init_db():
    """Initialize database (no-op for Supabase)"""
    pass
