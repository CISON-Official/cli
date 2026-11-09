import inspect
from pathlib import Path

from decouple import Config, RepositoryEnv, UndefinedValueError, config

CONFIG_DIR = Path.home() / ".cison"
ENV_PATH = CONFIG_DIR / ".env"

def get_config():
    package_src_dir = Path(__file__).resolve().parent
    
    local_env = None
    for parent in [package_src_dir, package_src_dir.parent, package_src_dir.parent.parent]:
        if (parent / ".env").exists() and (parent / "pyproject.toml").exists():
            local_env = parent / ".env"
            break

    if local_env:
        return Config(RepositoryEnv(local_env))
        
    if ENV_PATH.exists():
        print("using global env")
        return Config(RepositoryEnv(ENV_PATH))
        
    return config

class Settings:
    BASE_URL = "https://api.cison.org"
    ADMIN_EMAIL = ""
    ADMIN_CERTIFICATE_EXCHANGE_KEY = ""
    CELERY_HOST = ""
    ADMIN_CERTIFICATE_ROUTING_KEY = ""
    MEMBERSHIP_CERTIFICATION_TASK_NAME = ""
    PRECONFERENCE_2025_CERTIFICATION_TASK_NAME = ""
    PRECONFERENCE_2026_CERTIFICATION_TASK_NAME = ""
    CONFERENCE_2025_CERTIFICATION_TASK_NAME = ""
    CONFERENCE_2026_CERTIFICATION_TASK_NAME = ""
    FELLOWSHIP_CERTIFICATION_TASK_NAME = ""
    STUDENT_CERTIFICATION_TASK_NAME = ""
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


def env_key_from_line(line: str) -> str:
    """Extract the setting key from a .env line, or '' if the line holds no assignment."""
    stripped = line.strip()

    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return ""

    return stripped.split("=", 1)[0].strip()


def read_env_values(path: Path | None = None) -> dict[str, str]:
    """Read the key/value pairs stored in a .env file."""
    target = ENV_PATH if path is None else path

    if not target.exists():
        return {}

    values: dict[str, str] = {}
    for line in target.read_text().splitlines():
        key = env_key_from_line(line)
        if key:
            values[key] = line.split("=", 1)[1].strip()
    return values


def get_outstanding_setting_keys(path: Path | None = None) -> list[str]:
    """Return the setting keys that are absent or blank in the given .env file."""
    values = read_env_values(path)
    return [key for key in get_setting_keys() if not values.get(key, "").strip()]


def write_env_values(values: dict[str, str], path: Path | None = None) -> None:
    """Write values into a .env file, preserving unrelated lines, order and comments."""
    target = ENV_PATH if path is None else path
    pending = dict(values)
    lines: list[str] = []

    for line in read_env_lines(target):
        key = env_key_from_line(line)
        if key and key in pending:
            lines.append(f"{key}={pending.pop(key)}")
        else:
            lines.append(line)

    for key, value in pending.items():
        lines.append(f"{key}={value}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n")


def read_env_lines(path: Path | None = None) -> list[str]:
    """Return the raw lines of a .env file, or an empty list if it does not exist."""
    target = ENV_PATH if path is None else path

    if not target.exists():
        return []

    return target.read_text().splitlines()


def get_missing_setting_keys() -> list[str]:
    """Return the setting keys that are unset or blank in the active configuration."""
    if not ENV_PATH.exists():
        return get_setting_keys()

    cfg = get_config()
    missing: list[str] = []

    for key in get_setting_keys():
        try:
            val = cfg(key)
        except UndefinedValueError:
            missing.append(key)
            continue
        if val is None or str(val).strip() == "":
            missing.append(key)

    return missing


def is_configured() -> bool:
    """Validate that the .env file exists and contains all required dynamic keys."""
    return ENV_PATH.exists() and not get_missing_setting_keys()


setting = Settings()
