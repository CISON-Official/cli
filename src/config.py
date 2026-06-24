import os
from decouple import config

BASE_URL = "https://example.com"

# Easily expandable dictionary for URL shortcuts
SHORTCUTS = {"u": "/users", "p": "/posts", "status": "/system/health/status"}


def resolve_url(path_or_shortcut: str) -> str:
    """Resolves a shortcut alias to a full endpoint path."""
    path = SHORTCUTS.get(path_or_shortcut, path_or_shortcut)
    return f"{BASE_URL}{path}" if not path.startswith("http") else path


def get_headers(token: str) -> dict:
    """Global headers like Authentication."""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


class Settings:

    BASE_URL = config("BASE_URL")
    ADMIN_EMAIL = config("ADMIN_EMAIL")


setting = Settings()
