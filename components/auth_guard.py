import streamlit as st

from auth import get_current_role, is_authenticated


def auth_guard() -> None:
    if not is_authenticated():
        st.warning("🔒 Please log in to access this page.")
        st.page_link("app.py", label="Go to Login →", icon="🔑")
        st.stop()


def require_role(role: str) -> None:
    auth_guard()
    current = get_current_role()
    if current != role:
        role_label = "Venue Owner / Client" if role == "client" else "Musician"
        st.error(f"⛔ Access Denied — This section is for {role_label}s only.")
        if role == "client":
            st.info("Navigate to **Explore Gigs** or **My Applications** from the sidebar.")
        else:
            st.info("Navigate to **My Gigs** or **Applications** from the sidebar.")
        st.stop()


def require_client() -> None:
    require_role("client")


def require_musician() -> None:
    require_role("musician")
