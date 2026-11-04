import typer

from src.commands.certificates.conference import app as conference_app
from src.commands.certificates.membership import app as membership_app
from src.commands.certificates.preconference import app as preconference_app
from src.commands.certificates.prs import app as prs_app

app = typer.Typer(name="certificates")
app.add_typer(membership_app)
app.add_typer(prs_app)
app.add_typer(preconference_app)
app.add_typer(conference_app)
