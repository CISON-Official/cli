import typer

from src.commands.member_id import member_id_app

app = typer.Typer(help="CISON Commandline Interface")
app.add_typer(member_id_app)


if __name__ == "__main__":
    app()
