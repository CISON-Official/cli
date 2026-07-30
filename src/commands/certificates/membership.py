#!/usr/bin/env python3

import uuid
import logging
import json as ajson
from time import sleep
from typing import Optional
from datetime import datetime


import pika
import typer
import pandas as pd
from tqdm import tqdm
from rich import print
from requests import Session
from rich.table import Table
from rich.progress import track
from rich.console import Console

from src.commands.user import User
from src.decorators import api_caller, silence_stdout
from src.config import get_headers, print_error, setting

app = typer.Typer(name="membership")
console = Console()
logger = logging.getLogger(__name__)

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
        with open("sleeping.json", "w") as file:
            ajson.dump(response.json(), file)
        certificates = list(
            filter(
                lambda x: (x["member_id"] == member_id),
                response.json()["data"],
            )
        )
        print(certificates)
        if len(certificates) == 0:
            print("[red]User does not have a certificate[/red],")
            return False, None
        else:
            print("[green]User has a certificate[/green]")
            return True, certificates[0]

    @api_caller
    @staticmethod
    def create_certificates(
        member_id: str, user_id=Optional[int], **kwargs
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

        status, certificate = Membership.check_for_certificates(
            user_id=user_id, member_id=member_id
        )
        print(certificate)

        if not status:
            response = session.post(
                f"{root_url.rstrip('/')}/cert/add-new",
                headers=get_headers(token),
                json=dict(user_id=user_id, member_id=member_id),  # type: ignore
            )
            response.raise_for_status()

        cert_data = session.get(
            f"{root_url.rstrip('/')}/certificate",
            json=dict(user_id=user_id),  # type: ignore
            headers=get_headers(token),
        )
        cert_data.raise_for_status()
        new_user = list(
            filter(
                lambda x: (x["member_id"] == member_id),
                cert_data.json()["data"],
            )
        )[0]

        data = dict(
            name=f"{new_user['surname']} {new_user['firstname']} {new_user['middlename']}",
            current_date=datetime.fromtimestamp(
                float(new_user["date_issued"])
            ).strftime("%d/%m/%Y"),
            membership_id=str(member_id),
            certificate_id=str(new_user["cert_id"]),
            email=new_user["email"],
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

    @api_caller
    @staticmethod
    def list_qualified(**kwargs) -> None:

        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        response = session.get(
            f"{root_url.rstrip('/')}/cert/get-qualified-candidate",
            headers=get_headers(token),
            json=dict(email=setting.ADMIN_EMAIL),
        )

        data = response.json().get("data")

        if not data or len(data) <= 0:
            print("[green]All users have been Issued Certificates[/green]")
            return data

        for user in data:
            console.print(f"[green]✔[/green] Found candidate: {user.get("first_name")}")
        return data


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
    member_id: str = typer.Argument(..., help="Member ID of the user"),
):

    if not user_id and not member_id:
        print_error("Error: You must provide either --user-id or --member-id.")
        raise typer.BadParameter("Missing identifier.")
    print(f"Processing with user_id={user_id} and member_id={member_id}")
    Membership.create_certificates(member_id=member_id, user_id=None)


@app.command(
    name="get-eligible",
    help="CLI Command to get eligible members for issuing membership certificates",
)
def get_eligible(ctx: typer.Context):
    loader = ctx.obj
    logger.info("Retrieving members eligible for membership certificate...")

    if ctx.obj:
        ctx.obj.stop()

    eligible_members = Membership.list_qualified()

    if len(eligible_members) >= 1:
        table = Table(title="Eligible Candidates", show_footer=True)
        table.add_column("Name", style="cyan")
        table.add_column("Member ID", style="green")

        for member in eligible_members:
            table.add_row(
                f"{member['first_name']} {member['last_name']} {member['middle_name']}",
                member["member_id"],
            )

        console.print(table)

    else:
        console.print(
            "[yellow]⚠ No members are currently eligible for a membership certificate.[/yellow]"
        )
        raise typer.Exit(code=0)


@app.command(
    name="bulk-create-certificate",
    help="CLI command for triggering the bulk creation of membership certificate",
)
def create_bulk_certificates(
    ctx: typer.Context,
    member_ids: list[str] = typer.Argument(..., help="Bulk Member ID of all the users"),
):

    loader = ctx.obj

    # 1. Update the generic loader state message
    logger.info(f"Preparing data structures for {len(member_ids)} members...")
    sleep(1)

    print()

    for member_id in track(
        member_ids, description="[bold green]Bulk creating certificates..."
    ):
        with silence_stdout():
            Membership.create_certificates(member_id=member_id, user_id=None)

    console.print(
        "\n[bold green]✔ All certificates have been generated successfully![/bold green]"
    )
