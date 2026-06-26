#!/usr/bin/env python3

import typer

from src.commands.certificates.membership import app as membership_app
from src.commands.certificates.prs import app as prs_app

app = typer.Typer(name="certificates")
app.add_typer(membership_app)
app.add_typer(prs_app)
