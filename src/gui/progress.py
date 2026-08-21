"""Rich progress bar and spinner helpers for long-running CLI operations."""

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import contextmanager

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

console = Console()


@contextmanager
def step_progress(description: str, *, total: int) -> Generator[Callable[[int], None]]:
    """Context manager yielding an ``advance(n)`` callback backed by a Rich progress bar.

    Args:
        description: Label shown to the left of the progress bar.
        total: Total number of units of work expected.

    Yields:
        A callable that advances the progress bar by the given number of
        completed units.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_id = progress.add_task(description, total=total)

        def advance(amount: int = 1) -> None:
            progress.update(task_id, advance=amount)

        yield advance


@contextmanager
def spinner(message: str) -> Generator[None]:
    """Context manager showing an indeterminate spinner during a blocking call.

    Args:
        message: Message displayed next to the spinner.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(message, total=None)
        yield
