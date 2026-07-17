import os

from decouple import config
from rich.console import Console


def print_error(string: str) -> None:
    small_console = Console()
    small_console.bell()
    small_console.print(f"[red][bold] Error: [/bold]{string} [/red]")


def get_headers(token: str) -> dict:
    """Global headers like Authentication."""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

class Settings:

    BASE_URL = config("BASE_URL")
    ADMIN_EMAIL = config("ADMIN_EMAIL")
    ADMIN_CERTIFICATE_EXCHANGE_KEY = config("ADMIN_CERTIFICATE_EXCHANGE_KEY")
    CELERY_HOST = config("CELERY_HOST")
    ADMIN_CERTIFICATE_ROUTING_KEY = config("ADMIN_CERTIFICATE_ROUTING_KEY")
    MEMBERSHIP_CERTIFICATION_TASK_NAME = config("MEMBERSHIP_CERTIFICATION_TASK_NAME")


setting = Settings()
