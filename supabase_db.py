"""
Cliente Supabase — reemplaza SQLAlchemy para producción en Vercel.
Usa la REST API de Supabase (HTTP/HTTPS), compatible con cualquier entorno.
"""
from supabase import create_client, Client
from config import settings

_client: Client = None


def get_sb() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _client
