#!/usr/bin/env python3
import os
import sys
from functools import wraps
from typing import Callable
from contextlib import contextmanager

from requests import Session

from src.config import setting


def api_caller(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        with Session() as session:
            root_url = str(setting.BASE_URL)
            email = str(setting.ADMIN_EMAIL)
            response = session.post(
                root_url + "auth/api-key",
                json=dict(email=email),
            )
            if response.status_code >= 200 and response.status_code < 300:
                data = dict(
                    email=email,
                    token=response.json()["data"]["token"],
                    root_url=root_url,
                    session=session,
                )
                kwargs.update(data)
                return func(*args, **kwargs)
            else:
                raise Exception("Unable to authenticate user {}".format(response.text))

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
