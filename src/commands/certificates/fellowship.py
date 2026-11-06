from typing import Optional
import json as ajson
import logging
import uuid

import pika
import typer
from requests import Session, Response
from rich import print
from rich.console import Console

from src.config import setting
from src.decorators import api_caller
from src.utils import get_headers, clean_name

app = typer.Typer(name="fellowship")
console = Console()
logger = logging.getLogger(__name__)


def resolve_task_name(setting_name: str) -> str:
    task_name = str(getattr(setting, setting_name, "") or "")

    if not task_name:
        console.print(
            f"[red]✗ {setting_name} is not configured for fellowship certificate.[/red]"
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


class Fellowship:
    @api_caller
    @staticmethod
    def create_certificate(
        cert_name: str,
        registrant_email: str,
        fellowship_id: str,
        member_id: Optional[int] = None,
        **kwargs,
    ) -> None:

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

        print(f"Recording fellowship registration for {email}...")

        payload: dict[str, object] = {
            "email": email,
            "name": name,
            "fellowship_id": fellowship_id,
        }

        task_name = resolve_task_name("FELLOWSHIP_CERTIFICATION_TASK_NAME")

        publish(task_name, payload)

        console.print(f"[green]✔[/green] Fellowship certificate queued for " f"{name}")


@app.command(
    name="create",
    help="Register a paid fellowship attendee and queue their certificate",
)
def create_certificate(
    name: str = typer.Option(..., "--name", "-f", help="Full Name"),
    email: str = typer.Option(..., "--email", "-e", help="Registrant's e-mail"),
    fellowship_id: str = typer.Option(
        ..., "--fellowship-id", "-i", help="Fellowship ID"
    ),
    member_id: str = typer.Option(..., "--member-id", "-m", help="Member id"),
):

    Fellowship.create_certificate(
        cert_name=name,
        registrant_email=email,
        fellowship_id=fellowship_id,
        member_id=member_id,
    )


# @app.command(
#     name="queue",
#     help="Queue fellowship certificate",
# )
# def queue_certificate(
#     name: str = typer.Argument(..., help="Name of the certificate holder"),
#     email: str = typer.Argument(..., help="Email of the certificate holder"),
# ):

#     print("Creating fellowship certificate...")
#     task_name = resolve_task_name("FELLOWSHIP_CERTIFICATION_TASK_NAME")
#     publish(
#         task_name,
#         {
#             "name": name,
#             "email": email,
#         },
#     )
#     console.print(f"[green]✔ Fellowship certificate queued for {name}[/green]")
