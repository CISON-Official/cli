import json as ajson
import logging
import uuid

import pika
import typer
from requests import Response, Session
from rich.console import Console
from rich.table import Table

from src.config import setting
from src.decorators import api_caller
from src.utils import get_headers

app = typer.Typer(name="student")
console = Console()
logger = logging.getLogger(__name__)


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


def resolve_task_name(setting_name: str) -> str:
    task_name = str(getattr(setting, setting_name, "") or "")

    if not task_name:
        console.print(
            f"[red]✗ {setting_name} is not configured for student certificates.[/red]"
        )
        raise typer.Exit(code=1)

    return task_name


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


class Student:
    @api_caller
    @staticmethod
    def list_eligible(**kwargs) -> list[str]:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        response = session.get(
            f"{root_url.rstrip('/')}/student-certificate/eligible",
            headers=get_headers(token),
        )
        response.raise_for_status()
        return response.json().get("data") or []

    @api_caller
    @staticmethod
    def create_certificate(member_id: str, **kwargs) -> dict | None:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        task_name = resolve_task_name("STUDENT_CERTIFICATION_TASK_NAME")

        response = session.post(
            f"{root_url.rstrip('/')}/student-certificate/create",
            headers=get_headers(token),
            json={"member_id": member_id},
        )

        if response.status_code == 409:
            console.print(
                f"[yellow]![/yellow] A student certificate already exists for "
                f"member [bold]{member_id}[/bold]."
            )
            return None

        if response.status_code not in (200, 201):
            console.print(
                f"[red]✗ Could not create student certificate for member "
                f"{member_id}: {api_error_message(response)}[/red]"
            )
            raise typer.Exit(code=1)

        data = response.json().get("data") or {}
        name = data.get("student_name") or member_id
        console.print(f"[green]✔[/green] Student certificate created for {name}")

        publish(task_name, data)
        console.print(f"[green]✔[/green] Student certificate queued for {name}")
        return data

    @api_caller
    @staticmethod
    def delete_certificate(member_id: str, **kwargs) -> bool:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        response = session.delete(
            f"{root_url.rstrip('/')}/student-certificate/delete",
            headers=get_headers(token),
            params={"member_id": member_id},
        )

        if response.status_code == 404:
            console.print(
                f"[yellow]![/yellow] No student certificate found for member "
                f"[bold]{member_id}[/bold]."
            )
            return False

        if response.status_code != 200:
            console.print(
                f"[red]✗ Could not delete student certificate for member "
                f"{member_id}: {api_error_message(response)}[/red]"
            )
            raise typer.Exit(code=1)

        console.print(
            f"[green]✔[/green] Student certificate deleted for member {member_id}"
        )
        return True


@app.command(
    name="eligible",
    help="List students currently eligible for a student certificate",
)
def list_eligible() -> None:
    logger.info("Retrieving students eligible for student certificates...")

    eligible_members = Student.list_eligible()

    if not eligible_members:
        console.print(
            "[yellow]⚠ No students are currently eligible for a student "
            "certificate.[/yellow]"
        )
        raise typer.Exit(code=0)

    table = Table(title="Eligible Students")
    table.add_column("Member ID", style="green")

    for member_id in eligible_members:
        table.add_row(str(member_id))

    console.print(table)


@app.command(name="create", help="Create a student certificate for a member")
def create_certificate(
    member_id: str = typer.Argument(..., help="Member ID of the student"),
) -> None:
    Student.create_certificate(member_id=member_id)


@app.command(name="delete", help="Delete the student certificate for a member")
def delete_certificate(
    member_id: str = typer.Argument(..., help="Member ID of the student"),
) -> None:
    Student.delete_certificate(member_id=member_id)
