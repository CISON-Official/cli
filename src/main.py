#!/usr/bin/env python3
import logging
import subprocess

import typer
from rich.console import Console
from rich.table import Table

from src.loader import LoggingManager
from src.config import (
    is_configured,
    get_setting_keys,
    ENV_PATH,
    CONFIG_DIR,
    get_config,
    Settings,
)
from src.send import app as send_app
from src.email import app as email_app
from src.commands.user import app as user_app
from src.utils import clear_disk_cache, USER_CACHE_DIR
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
        typer.secho(
            "\n[!] CISON CLI is not configured or has missing parameters.",
            fg=typer.colors.YELLOW,
            bold=True,
        )
        typer.secho(
            f"Configuration file check failed at: {ENV_PATH}\n"
            "Please run the setup command to configure all environment variables:\n\n"
            "   cison configure\n",
            fg=typer.colors.WHITE,
        )
        raise typer.Exit(code=1)


@app.command("configure")
def configure(
    overwrite: bool = typer.Option(
        False, "--overwrite", "-o", help="Overwrite existing configuration from scratch"
    ),
):
    """
    Dynamically configure all environment variables defined in Settings.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = get_config() if ENV_PATH.exists() else None

    typer.secho(
        "\n=== Dynamic CISON CLI Configuration ===", fg=typer.colors.CYAN, bold=True
    )
    typer.secho(f"Target file: {ENV_PATH}\n", fg=typer.colors.WHITE)

    env_data = {}
    keys = get_setting_keys()

    sensitive_keywords = ["SECRET", "KEY", "TOKEN", "PASSWORD"]

    for key in keys:
        existing_val = ""
        if cfg and not overwrite:
            existing_val = cfg(key, default="")
        if not existing_val:
            existing_val = getattr(Settings, key, "")

        is_sensitive = any(kw in key for kw in sensitive_keywords)

        # Prompt user dynamically for each setting variable
        user_val = typer.prompt(
            f"Enter {key}",
            default=existing_val if existing_val else None,
            hide_input=is_sensitive,
        )
        env_data[key] = str(user_val).strip()

    # Write out .env file dynamically
    env_content = "\n".join([f"{k}={v}" for k, v in env_data.items()]) + "\n"
    ENV_PATH.write_text(env_content)

    typer.secho(
        f"\n✓ Successfully configured {len(keys)} environment parameters at {ENV_PATH}",
        fg=typer.colors.GREEN,
        bold=True,
    )


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
