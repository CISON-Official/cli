import typer

from src.loader import GlobalLoader
from src.commands.user import app as user_app
from src.commands.member_id import app as memberid_app
from src.commands.certificates import app as certificate_app

app = typer.Typer(help="CISON Commandline Interface")
loader = GlobalLoader()

app.add_typer(user_app)
app.add_typer(memberid_app)
app.add_typer(certificate_app)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    This callback runs BEFORE any command or subcommand executes.
    """
    if ctx.invoked_subcommand is not None:
        ctx.obj = loader
        cmd_name = ctx.invoked_subcommand
        loader.start(f"Running '{cmd_name}'... Please wait.")
    ctx.call_on_close(loader.stop)




if __name__ == "__main__":
    app()
