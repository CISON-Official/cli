#!/usr/bin/env python3

import uuid
import typer
import json as ajson
from typing import Optional
from datetime import datetime

import pika
import pandas as pd
from requests import Session

from src.commands.user import User
from src.decorators import api_caller
from src.config import get_headers, print_error, setting

app = typer.Typer(name="membership")


class Membership:

    @api_caller
    @staticmethod
    def get_membership_certificate(user_id: int, **kwargs) -> Optional[dict[str, str]]:

        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        response = session.get(
            f"{root_url.rstrip('/')}/certificate",
            headers=get_headers(token),
            json=dict(user_id=user_id),
        )
        response.raise_for_status()

    @api_caller
    @staticmethod
    def check_for_certificates(
        member_id: Optional[int] = None, user_id: Optional[int] = None, **kwargs
    ) -> tuple[bool, Optional[dict]]:

        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        user_id = (
            user_id if user_id else User.get_user_id_from_member_id(member_id=member_id)
        )

        response = session.get(
            f"{root_url.rstrip('/')}/certificate",
            headers=get_headers(token),
            json=dict(user_id=user_id),
        )
        response.raise_for_status()
        certificates = list(
            filter(
                lambda x: int(x["member_id"]) == member_id,
                response.json()["data"],
            )
        )

        if len(certificates) == 0:
            print("User does not have a certificate")
            return False, None
        else:
            print("User has a certificate")
            return True, certificates[0]

    @api_caller
    @staticmethod
    def create_certificates(
        member_id: Optional[int] = None, user_id=Optional[int], **kwargs
    ) -> Optional[dict]:

        # try:
        print("Creating certificate...")

        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        user_id = (
            user_id if user_id else User.get_user_id_from_member_id(member_id=member_id)
        )

        print(member_id, user_id)

        status, certificate = Membership.check_for_certificates(user_id=user_id, member_id=member_id)
        print(certificate)

        if status:
            print("Process Ended")
            return

        response = session.post(
            f"{root_url.rstrip('/')}/cert/add-new",
            headers=get_headers(token),
            json=dict(user_id=user_id),  # type: ignore
        )
        response.raise_for_status()

        data = dict(
            name=f"{certificate['surname']} {certificate['firstname']} {certificate['middlename']}",
            current_date=datetime.fromtimestamp(
                float(certificate["date_issued"])
            ).strftime("%d/%m/%Y"),
            membership_id=str(certificate["member_id"]),
            certificate_id=str(certificate["cert_id"]),
            email=certificate["email"],
        )

        connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))  # type: ignore
        channel = connection.channel()
        task_id = str(uuid.uuid4())

        body = ajson.dumps([[], data, {}]).encode("utf-8", "ignore")

        headers = {
            "lang": "py",
            "task": setting.MEMBERSHIP_CERTIFICATION_TASK_NAME,
            "id": task_id,
            "retries": 5,
            "timelimit": [30000, None],
            "origin": "pika-producer",
        }

        channel.basic_publish(
            exchange=str(setting.ADMIN_CERTIFICATE_EXCHANGE_KEY),
            routing_key=str(setting.ADMIN_CERTIFICATE_ROUTING_KEY),
            body=body,
            properties=pika.BasicProperties(
                content_type="application/json",
                content_encoding="utf-8",
                headers=headers,
                delivery_mode=2,
            ),
        )
        connection.close()

    # except Exception as e:
    #     print(e)


@app.command(
    name="have-certificate",
    help="Checking whether a user with member_id have certificate",
)
def checking_if_a_user_have_certificate(
    member_id=typer.Argument(..., help="member_id of a user to get the actual ID")
):
    Membership.check_for_certificates(member_id)


@app.command(
    name="create-certificate",
    help="CLI command for triggering membership certificate creation",
)
def create_certificates(
    user_id: Optional[int] = typer.Option(
        None, "--user-id", "-u", help="The actual user ID"
    ),
    member_id: Optional[int] = typer.Option(
        None, "--member-id", "-m", help="Member ID of the user"
    ),
):

    if not user_id and not member_id:
        print_error("Error: You must provide either --user-id or --member-id.")
        raise typer.BadParameter("Missing identifier.")
    print(f"Processing with user_id={user_id} and member_id={member_id}")
    if user_id:
        Membership.create_certificates(user_id=user_id, member_id=None)
        return
    Membership.create_certificates(member_id=member_id, user_id=None)
