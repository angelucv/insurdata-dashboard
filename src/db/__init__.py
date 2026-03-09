# src.db - Persistencia Supabase/PostgreSQL
from .client import get_supabase_client, get_supabase_anuario_client, load_df_into_table
from .schema import SCHEMA_SQL

__all__ = ["get_supabase_client", "get_supabase_anuario_client", "load_df_into_table", "SCHEMA_SQL"]
