#!/usr/bin/env python3


from src.__email import get_access_token, get_email_header


class EmailBase:

    def __init__(self) -> None:

        self.access_token = get_access_token()
        self.params: dict[str, list | int | str | bool | None] = dict(resfmt="JSON")

    def get_header(self) -> dict:
        return get_email_header(self.access_token)
