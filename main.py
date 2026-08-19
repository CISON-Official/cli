#!/usr/bin/env python3
import logging

import typer

from src.loader import LoggingManager
from src.send import app as send_app
from src.email import app as email_app
from src.commands.user import app as user_app
from src.commands.member_id import app as memberid_app
from src.commands.certificates import app as certificate_app

LoggingManager.setup_logging(base_dir="logs", log_level=logging.INFO)

app = typer.Typer(
    name="CISON CLI",
    help="CISON Commandline Interface",
    no_args_is_help=True,
    add_completion=True,
    rich_markup_mode="rich",
)

app.add_typer(user_app)
app.add_typer(send_app)
app.add_typer(email_app)
app.add_typer(memberid_app)
app.add_typer(certificate_app)


if __name__ == "__main__":
    app()
