import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_SECRET_KEY", "")

# We use the service role / secret key on the backend to bypass RLS when necessary,
# or to verify tokens. Ensure you don't leak this to the frontend.
supabase: Optional[Client] = None
if url and key:
    supabase = create_client(url, key)
