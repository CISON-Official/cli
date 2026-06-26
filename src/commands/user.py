#!/usr/bin/env python3

import typer
from rich import print
from typing import Optional

from requests import Session
from requests.exceptions import HTTPError

from src.decorators import api_caller
from src.config import get_headers, print_error
from src.gui.display_user import display_user_details

app = typer.Typer(name="user")


class User:

    @api_caller
    @staticmethod
    def get_user_id_from_member_id(member_id: int, **kwargs) -> Optional[None]:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/user_id",
                headers=get_headers(token),
                json=dict(member_id=member_id),
            )

            response.raise_for_status()

            if "user_id" in response.json():
                print(
                    'User ID for ->{}<- Member ID is "{}"'.format(
                        member_id, response.json().get("user_id")
                    )
                )
                return response.json().get("user_id")
        except HTTPError:
            print_error("Member ID Could not be found")
            return None

    @api_caller
    @staticmethod
    def get_user_information(user_id: int, **kwargs) -> Optional[dict[str, str]]:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/user",
                headers=get_headers(token),
                json=dict(user_id=user_id),
            )

            response.raise_for_status()

            if "data" in response.json():
                if "user_id" in response.json()["data"]:
                    if response.json()["data"]["user_id"].strip() != "":
                        return response.json()["data"]
                    else:
                        print_error("User ID is not found in dataset")
                        return None
                else:
                    print_error("Dataset returned is empty")
                    return None
            else:
                print_error("Dataset is an invalid response")
                return None
        except HTTPError:
            print_error("Member ID Could not be found")
            return None


@app.command(name="get-memberid")
def get_user_id_from_member_id(
    member_id=typer.Argument(..., help="member_id of a user to get the actual ID")
):
    User.get_user_id_from_member_id(member_id)


@app.command(name="about")
def get_user_information(user_id=typer.Argument(..., help="The actual ID of a user")):
    response = User.get_user_information(user_id)
    if response:
        display_user_details(response)


@app.command(name="uifmid", help="User Information from Member ID")
def get_user_information_from_member_id(
    member_id=typer.Argument(..., help="member_id of a user to get the actual ID")
):
    response1 = User.get_user_id_from_member_id(member_id)
    if response1:
        response2 = User.get_user_information(response1)
        if response2:
            display_user_details(response2)
