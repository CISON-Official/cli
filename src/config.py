import inspect
from pathlib import Path

from decouple import Config, RepositoryEnv, UndefinedValueError

CONFIG_DIR = Path.home() / ".cison"
ENV_PATH = CONFIG_DIR / ".env"


def get_config():
    """Load config from ~/.cison/.env or fall back to decouple defaults."""
    if ENV_PATH.exists():
        return Config(RepositoryEnv(ENV_PATH))
    from decouple import config

    return config


class Settings:
    BASE_URL = "https://api.cison.org"
    ADMIN_EMAIL = ""
    ADMIN_CERTIFICATE_EXCHANGE_KEY = ""
    CELERY_HOST = ""
    ADMIN_CERTIFICATE_ROUTING_KEY = ""
    MEMBERSHIP_CERTIFICATION_TASK_NAME = ""
    EMAIL_API_BASE = ""
    CLIENT_ID = ""
    CLIENT_SECRET = ""
    REFRESH_TOKEN = ""
    EMAIL_ADMIN = ""
    PROGRAM_NAME = ""
    CLOUDFLARE_ZONE_ID = ""
    CLOUDFLARE_API_TOKEN = ""
    CLOUDFLARE_MAIN_DOMAIN = ""
    CLOUDFLARE_IP_ADDRESS = ""
    CLOUDFLARE_SUBDOMAIN = ""
    UPLOAD_ID = ""
    MAILINGLIST_LIMIT = ""
    TEST_USEREMAIL_1 = ""
    TEST_USEREMAIL_2 = ""
    TEST_USEREMAIL_3 = ""
    TEST_USEREMAIL_4 = ""
    TEST_USEREMAIL_5 = ""
    TEST_USEREMAIL_6 = ""
    TEST_USEREMAIL_7 = ""
    TEST_USEREMAIL_8 = ""
    TEST_USEREMAIL_9 = ""
    TEST_USEREMAIL_10 = ""

    def __init__(self):
        cfg = get_config()
        # Dynamically bind all uppercase class variables from decouple/env
        for key in get_setting_keys():
            setattr(self, key, cfg(key, default=getattr(self.__class__, key, "")))


def get_setting_keys() -> list[str]:
    """Dynamically return all non-private uppercase attribute keys defined on Settings."""
    return [
        attr
        for attr, val in inspect.getmembers(Settings)
        if attr.isupper() and not attr.startswith("_")
    ]


def is_configured() -> bool:
    """Validate that the .env file exists and contains all required dynamic keys."""
    if not ENV_PATH.exists():
        return False

    cfg = get_config()
    for key in get_setting_keys():
        try:
            val = cfg(key)
            if val is None or str(val).strip() == "":
                return False
        except UndefinedValueError:
            return False
    return True


setting = Settings()
