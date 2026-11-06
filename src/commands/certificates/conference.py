import json as ajson
import logging
from typing import Optional
import uuid

import pika
import typer
from rich import print
from rich.console import Console
from requests import Session, Response

from src.config import setting
from src.decorators import api_caller
from src.utils import get_headers, clean_name

app = typer.Typer(name="conference")
console = Console()
logger = logging.getLogger(__name__)


def resolve_task_name(setting_name: str, year: int) -> str:
    task_name = str(getattr(setting, setting_name, "") or "")

    if not task_name:
        console.print(
            f"[red]✗ {setting_name} is not configured for the {year} conference "
            f"certificate.[/red]"
        )
        raise typer.Exit(code=1)

    return task_name


def api_error_message(response: Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text.strip() or f"HTTP {response.status_code}"

    if not isinstance(body, dict):
        return f"HTTP {response.status_code}"

    code = str(body.get("code") or "").strip()
    message = str(body.get("message") or "").strip()

    if code and message:
        return f"{code} ({response.status_code}): {message}"

    return f"HTTP {response.status_code}"


def publish(task_name: str, data: dict) -> None:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=setting.CELERY_HOST)
    )  # type: ignore
    channel = connection.channel()
    task_id = str(uuid.uuid4())

    body = ajson.dumps([[], data, {}]).encode("utf-8", "ignore")

    headers = {
        "lang": "py",
        "task": task_name,
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


class Conference:
    @api_caller
    @staticmethod
    def create_2025_certificate(
        cert_name: str,
        registrant_email: str,
        order_id: int,
        member_id: str | None = None,
        **kwargs,
    ) -> None:

        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        print(f"Recording 2025 conference registration...")

        if member_id:
            cert_response = session.get(
                f"{root_url.rstrip("/")}/cert/get-cert-name?member_id={member_id}",
                headers=get_headers(token),
            )
            data = cert_response.json().get("data")
            if data and data.get("certificate_name"):
                name = data.get("certificate_name")
            else:
                name = f'{clean_name(data.get("first_name"))} {clean_name(data.get("middle_name"))} {clean_name(data.get("last_name"))}'

            email = data.get("email")
        else:
            name = cert_name
            email = registrant_email

        payload = dict(
            name=name,
            certificate_id=order_id,
            email=email,
            first_name=name.split(" ")[0],
            surname=name.split(" ")[-1],
        )

        response = session.post(
            f"{root_url.rstrip('/')}/cert/add-2025-conference",
            headers=get_headers(token),
            json=payload,
        )

        if response.status_code == 400:
            try:
                code = response.json().get("code")
            except ValueError:
                code = None

            if code == "already_exists":
                console.print(
                    f"[yellow]![/yellow] A 2025 conference registration already "
                    f"exists for [bold]{email}[/bold]; no certificate was queued."
                )
                return

        if response.status_code != 200:
            console.print(
                f"[red]✗ Could not register {email}: "
                f"{api_error_message(response)}[/red]"
            )
            raise typer.Exit(code=1)

        console.print(
            f"[green]✔[/green] 2025 conference registration saved for {email}"
        )

        task_name = resolve_task_name("CONFERENCE_2025_CERTIFICATION_TASK_NAME", 2025)

        publish(task_name, payload)

        console.print(f"[green]✔[/green] 2025 conference certificate queued for {name}")

    @api_caller
    @staticmethod
    def create_2026_certificate(
        cert_name: str, registrant_email: str, member_id: Optional[int] = None, **kwargs
    ) -> None:

        print("Creating 2026 conference certificate...")

        task_name = resolve_task_name("CONFERENCE_2026_CERTIFICATION_TASK_NAME", 2026)

        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        response = session.get(
            f"{root_url.rstrip("/")}/cert/get-cert-name?member_id={member_id}",
            headers=get_headers(token),
        )

        data = response.json().get("data")
        if member_id:
            if data and data.get("certificate_name"):
                name = data.get("certificate_name")
            else:
                name = f'{clean_name(data.get("first_name"))} {clean_name(data.get("middle_name"))} {clean_name(data.get("last_name"))}'

            email = data.get("email")
        else:
            name = cert_name
            email = registrant_email

        publish(
            task_name,
            {
                "name": name,
                "email": email,
                "member_id": member_id,
            },
        )

        console.print(f"[green]✔ 2026 conference certificate queued for {name}[/green]")


@app.command(
    name="2025",
    help="Register a paid 2025 conference attendee and queue their certificate",
)
def create_2025_certificate(
    name: str = typer.Argument(..., help="certificate name"),
    email: str = typer.Argument(..., help="Registrant's e-mail"),
    order_id: int = typer.Argument(..., help="Payment order reference"),
    member_id: Optional[int] = typer.Option(
        None, "-m", "--member-id", help="Member ID of the certificate holder"
    ),
):

    Conference.create_2025_certificate(
        cert_name=name, registrant_email=email, order_id=order_id, member_id=member_id
    )


@app.command(
    name="2026",
    help="CLI command for triggering 2026 conference certificate creation",
)
def create_2026_certificate(
    name: str = typer.Argument(..., help="Name of the certificate holder"),
    email: str = typer.Argument(..., help="Email of the certificate holder"),
    member_id: Optional[int] = typer.Option(
        None, "-m", "--member-id", help="Member ID of the certificate holder"
    ),
):

    Conference.create_2026_certificate(
        cert_name=name, registrant_email=email, member_id=member_id
    )
