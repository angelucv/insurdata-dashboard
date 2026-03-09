# src/app/components/auth.py
"""Capa de autenticación opcional con Supabase Auth (OIDC/OAuth 2.0)."""
import streamlit as st

from config.settings import SUPABASE_URL, SUPABASE_KEY, REQUIRE_AUTH


def check_auth_required() -> bool:
    """True si se debe exigir login (Supabase configurado y REQUIRE_AUTH=true)."""
    return bool(SUPABASE_URL and SUPABASE_KEY and REQUIRE_AUTH)


def get_supabase_auth():
    """Cliente de auth de Supabase si está disponible."""
    if not check_auth_required():
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY).auth
    except Exception:
        return None


def render_login_or_session():
    """
    Si la app requiere auth, muestra login o sesión.
    En Streamlit la sesión se puede guardar en st.session_state para persistir entre reruns.
    """
    if not check_auth_required():
        return True
    auth = get_supabase_auth()
    if auth is None:
        return True
    try:
        session = auth.get_session()
        if session and session.user:
            st.sidebar.success(f"Sesión: {session.user.email}")
            return True
    except Exception:
        pass
    # Sesión en estado para no depender de cookies entre reruns
    if st.session_state.get("supabase_authenticated"):
        return True
    with st.form("login"):
        email = st.text_input("Correo")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Iniciar sesión"):
            try:
                auth.sign_in_with_password({"email": email, "password": password})
                st.session_state["supabase_authenticated"] = True
                st.rerun()
            except Exception as e:
                st.error(str(e))
    return False


def logout_button():
    """Cierra sesión en Supabase Auth."""
    auth = get_supabase_auth()
    if auth and st.sidebar.button("Cerrar sesión"):
        try:
            auth.sign_out()
        except Exception:
            pass
        st.session_state.pop("supabase_authenticated", None)
        st.rerun()
