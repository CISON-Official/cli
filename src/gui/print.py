#!/usr/bin/env python3

from typing import Any

from rich.json import JSON
from rich.panel import Panel
from rich.console import Console
from rich.prompt import Confirm, get_console


def print_success_panel(message: str, *, title: str = "Success") -> None:
    """Print a green success panel.

    Args:
        message: The message body to display.
        title: Panel title.
    """
    console = get_console()
    console.print(
        Panel(message, title=f"[bold green]{title}[/bold green]", border_style="green")
    )


def print_error_panel(message: str, *, title: str = "Error") -> None:
    """Print a red error panel.

    Args:
        message: The message body to display.
        title: Panel title.
    """
    console = get_console()
    console.print(
        Panel(message, title=f"[bold red]{title}[/bold red]", border_style="red")
    )


def print_warning_panel(message: str, *, title: str = "Warning") -> None:
    """Print a yellow warning panel.

    Args:
        message: The message body to display.
        title: Panel title.
    """
    console = get_console()
    console.print(
        Panel(
            message, title=f"[bold yellow]{title}[/bold yellow]", border_style="yellow"
        )
    )


def print_info_panel(message: str, *, title: str = "Info") -> None:
    """Print a blue informational panel.

    Args:
        message: The message body to display.
        title: Panel title.
    """
    console = get_console()
    console.print(
        Panel(message, title=f"[bold blue]{title}[/bold blue]", border_style="blue")
    )


def print_json(data: dict[str, Any] | list[Any], *, title: str | None = None) -> None:
    """Pretty-print a dictionary or list as syntax-highlighted JSON.

    Args:
        data: The JSON-serializable data to render.
        title: Optional panel title to wrap the JSON output in.

    Example:
        >>> print_json({"status": "success"}, title="Response")  # doctest: +SKIP
    """
    import json

    console = get_console()
    rendered = JSON(json.dumps(data, default=str))
    if title:
        console.print(Panel(rendered, title=title, border_style="cyan"))
    else:
        console.print(rendered)


def confirm_action(prompt: str, *, default: bool = False) -> bool:
    """Prompt the user for a yes/no confirmation before a destructive action.

    Args:
        prompt: The question to ask the user.
        default: The default answer if the user presses enter without typing.

    Returns:
        True if the user confirmed, False otherwise.
    """
    console = get_console()
    return Confirm.ask(prompt, default=default, console=console)
