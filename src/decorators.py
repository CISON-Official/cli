import os
import sys
import json
from datetime import datetime
from functools import wraps
from collections.abc import Callable
from contextlib import contextmanager

from requests import Session

from src.config import setting


def error_handler(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            os.makedirs(f"error/{func.__name__}/", exist_ok=True)
            with open(f"error/{func.__name__}/{datetime.now()}.json", "w") as f:
                data = {
                    "name": func.__name__,
                    "list_args": args,
                    "key_value_args": kwargs,
                    "error": str(e.__repr__()),
                }
                json.dump(data, f)

    return wrapper


def api_caller(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        with Session() as session:
            root_url = str(setting.BASE_URL)
            email = str(setting.ADMIN_EMAIL)
            response = session.post(
                root_url + "auth/api-key",
                json={"email": email},
            )
            if response.status_code >= 200 and response.status_code < 300:
                data = {
                    "email": email,
                    "token": response.json()["data"]["token"],
                    "root_url": root_url,
                    "session": session,
                }
                kwargs.update(data)
                return func(*args, **kwargs)
            else:
                raise Exception(f"Unable to authenticate user {response.text}")

    return wrapper


@contextmanager
def silence_stdout():
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stdout = old_stdout
