import os

import requests
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
    EMAIL_API_BASE = config("EMAIL_API_BASE")
    CLIENT_ID = config("CLIENT_ID")
    CLIENT_SECRET = config("CLIENT_SECRET")
    REFRESH_TOKEN = config("REFRESH_TOKEN")
    EMAIL_ADMIN = config("EMAIL_ADMIN")
    PROGRAM_NAME = config("PROGRAM_NAME")
    CLOUDFLARE_ZONE_ID = config("CLOUDFLARE_ZONE_ID")
    CLOUDFLARE_API_TOKEN = config("CLOUDFLARE_API_TOKEN")
    CLOUDFLARE_MAIN_DOMAIN = config("CLOUDFLARE_MAIN_DOMAIN")
    CLOUDFLARE_IP_ADDRESS = config("CLOUDFLARE_IP_ADDRESS")
    CLOUDFLARE_SUBDOMAIN = config("CLOUDFLARE_SUBDOMAIN")
    UPLOAD_ID = config("UPLOAD_ID")


setting = Settings()
