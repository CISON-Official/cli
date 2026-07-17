#!/usr/bin/env python3
from rich.console import Console

console = Console()


class GlobalLoader:
    def __init__(self):
        self._status = None

    def start(self, message: str):
        self._status = console.status(f"[bold blue]{message}", spinner="dots")
        self._status.start()

    def update(self, message: str, style: str = "bold blue"):
        if self._status:
            self._status.update(f"[{style}]{message}[/{style}]\n\n")

    def stop(self):
        if self._status:
            self._status.stop()
