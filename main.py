import typer

from src.commands.member_id import app as memberid_app
from src.commands.user import app as user_app
from src.commands.certificates import app as certificate_app

app = typer.Typer(help="CISON Commandline Interface")
app.add_typer(user_app)
app.add_typer(memberid_app)
app.add_typer(certificate_app)


if __name__ == "__main__":
    app()
