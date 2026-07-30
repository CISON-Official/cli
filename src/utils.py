#!/usr/bin/env python3
import time
from itertools import permutations

from rich.live import Live
from rich.text import Text


def count_occurenance(data: dict) -> dict:
    counter: dict[str, int] = dict()
    for j in data:
        k = j.get("fees")
        if not (outstanding := k.get("unpaid")):
            print("continuing")
            continue
        for i in outstanding.keys():
            if not counter.get(i):
                counter[i] = 0
            counter[i] = counter[i] + 1
    return counter


def find_sub_combinations(data: list) -> dict[tuple, int]:
    counter: dict[tuple, int] = dict()

    for j in data:
        if not isinstance(j, dict):
            continue

        k = j.get("fees", {})
        if not k or not (outstanding := k.get("unpaid")):
            print("continue")
            continue

        current_perms = set(permutations(outstanding.keys()))
        existing_keys = set(counter.keys())
        matching_keys = existing_keys & current_perms

        if matching_keys:
            matched_key = list(matching_keys)[0]
            counter[matched_key] += 1
            continue

        new_key = list(current_perms)[0]
        counter[new_key] = 1

    return counter


def count_down(x: int) -> None:
    session = Live(transient=True, refresh_per_second=4)
    session.start()

    try:
        while x >= 0:
            hours = x // 3600
            minutes = (x % 3600) // 60
            seconds = x % 60

            time_format = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            display_text = Text(f"Time Remaining: {time_format}", style="bold cyan")

            session.update(display_text)
            time.sleep(1)
            x -= 1

    finally:
        session.stop()
