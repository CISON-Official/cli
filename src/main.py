import logging
import subprocess

import typer
from rich.console import Console
from rich.table import Table

from src.commands.certificates import app as certificate_app
from src.commands.transactions import app as transaction_app
from src.commands.member_id import app as memberid_app
from src.commands.user import app as user_app
from src.config import (
    CONFIG_DIR,
    ENV_PATH,
    Settings,
    get_missing_setting_keys,
    get_outstanding_setting_keys,
    get_setting_keys,
    is_configured,
    read_env_values,
    write_env_values,
)
from src.email import app as email_app
from src.loader import LoggingManager
from src.send import app as send_app
from src.utils import USER_CACHE_DIR, clear_disk_cache

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
app.add_typer(transaction_app)

INTERNAL_REPO_URL = "git+ssh://git@github.com/CISON-Official/cli.git"


@app.callback()
def main_check(ctx: typer.Context):
    """
    Global interceptor checking if CLI configuration exists before execution.
    """
    allowed_unconfigured = ["configure", "self-update"]

    if ctx.invoked_subcommand in allowed_unconfigured or ctx.resilient_parsing:
        return

    if not is_configured():
        missing = get_missing_setting_keys()
        typer.secho(
            f"\n[!] CISON CLI is not configured ({len(missing)} setting(s) outstanding).",
            fg=typer.colors.YELLOW,
            bold=True,
        )
        for key in missing:
            typer.secho(f"    - {key}", fg=typer.colors.YELLOW)
        typer.secho(
            f"Configuration file: {ENV_PATH}\n"
            "Fill in only the outstanding settings with:\n\n"
            "   cison configure\n",
            fg=typer.colors.WHITE,
        )
        raise typer.Exit(code=1)


@app.command("configure")
def configure(
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        "-o",
        help="Re-enter every setting instead of only the outstanding ones",
    ),
):
    """
    Configure the environment variables defined in Settings.

    Only outstanding (absent or blank) values are prompted for. Values already
    present are preserved untouched unless --overwrite is given.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    keys = get_setting_keys()
    exists = ENV_PATH.exists()
    outstanding = keys if overwrite or not exists else get_outstanding_setting_keys()

    typer.secho("\n=== CISON CLI Configuration ===", fg=typer.colors.CYAN, bold=True)
    typer.secho(f"Target file: {ENV_PATH}\n", fg=typer.colors.WHITE)

    if not outstanding:
        typer.secho(
            f"✓ All {len(keys)} settings are already configured. Nothing to do.",
            fg=typer.colors.GREEN,
            bold=True,
        )
        raise typer.Exit(code=0)

    typer.secho(
        f"{len(outstanding)} of {len(keys)} settings outstanding:",
        fg=typer.colors.YELLOW,
    )
    for key in outstanding:
        typer.secho(f"  - {key}", fg=typer.colors.YELLOW)
    typer.secho("")

    existing_values = read_env_values() if exists else {}
    sensitive_keywords = ["SECRET", "KEY", "TOKEN", "PASSWORD"]

    env_data: dict[str, str] = {}

    for key in outstanding:
        existing_val = existing_values.get(key, "")
        is_sensitive = any(kw in key for kw in sensitive_keywords)

        user_val = typer.prompt(
            f"Enter {key}",
            default=existing_val if existing_val else None,
            hide_input=is_sensitive,
        )
        env_data[key] = str(user_val).strip()

    write_env_values(env_data)

    typer.secho(
        f"\n✓ Configured {len(env_data)} outstanding setting(s) at {ENV_PATH}",
        fg=typer.colors.GREEN,
        bold=True,
    )

    remaining = get_outstanding_setting_keys()
    if remaining:
        typer.secho(f"[!] Still blank: {', '.join(remaining)}", fg=typer.colors.YELLOW)


@app.command("update")
def self_update():
    """Update CISON CLI to latest version via uv."""
    typer.secho("Updating CISON CLI...", fg=typer.colors.CYAN)
    cmd = ["uv", "tool", "install", "--force", INTERNAL_REPO_URL]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        typer.secho(
            "✓ CISON CLI updated successfully!", fg=typer.colors.GREEN, bold=True
        )
    else:
        typer.secho(f"✗ Update failed:\n{result.stderr}", fg=typer.colors.RED, err=True)


config_app = typer.Typer(
    help="Manage and view CLI configuration.", no_args_is_help=True
)
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show():
    """Display current active configuration values with masked secrets."""
    """
    Display current active configuration values with masked secrets.
    """
    if not ENV_PATH.exists():
        typer.secho(
            f"[!] Configuration file does not exist at {ENV_PATH}. Run 'cison configure' first.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    console = Console()
    settings = Settings()
    keys = get_setting_keys()

    table = Table(
        title=f"CISON CLI Active Configuration ([dim]{ENV_PATH}[/dim])",
        show_header=True,
        header_style="bold cyan",
        title_justify="left",
    )
    table.add_column("Setting Variable", style="bold white")
    table.add_column("Configured Value", style="green")
    table.add_column("Status", style="dim white")

    sensitive_keywords = ["SECRET", "KEY", "TOKEN", "PASSWORD"]

    for key in sorted(keys):
        val = str(getattr(settings, key, "") or "")
        is_sensitive = any(kw in key for kw in sensitive_keywords)

        if not val:
            display_val = "[dim red]<Not Set>[/dim red]"
            status = "Missing"
        elif is_sensitive:
            # Mask sensitive values showing only the last 4 characters if long enough
            if len(val) > 8:
                display_val = f"{'*' * (len(val) - 4)}{val[-4:]}"
            else:
                display_val = "********"
            status = "Masked Secret"
        else:
            display_val = val
            status = "Active"

        table.add_row(key, display_val, status)

    console.print()
    console.print(table)
    console.print()


@config_app.command("cache-clear")
def cache_clear(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force cache clearance without confirmation prompt"
    ),
):
    """
    Clear all persistent disk-backed cache files (~/.cison/.cache/).
    """
    if not USER_CACHE_DIR.exists() or not any(USER_CACHE_DIR.iterdir()):
        typer.secho("✓ Cache is already empty.", fg=typer.colors.GREEN)
        return

    if not force:
        confirm = typer.confirm(
            f"Are you sure you want to delete all cache files in {USER_CACHE_DIR}?"
        )
        if not confirm:
            typer.secho("Operation cancelled.", fg=typer.colors.YELLOW)
            raise typer.Abort()

    clear_disk_cache()
    typer.secho(
        "✓ Successfully cleared all disk cache files!", fg=typer.colors.GREEN, bold=True
    )


if __name__ == "__main__":
    app()
