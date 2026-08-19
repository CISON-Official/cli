#!/usr/bin/env python3

import typer
import pandas as pd
from rich import print
from requests import Session


from src.utils import get_headers
from src.decorators import api_caller

app = typer.Typer(name="memberid")


class MemberID:
    @api_caller
    @staticmethod
    def get_next_member_id(member_id_prefix: str, **kwargs) -> str:

        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        response = session.get(
            f"{root_url.rstrip('/')}/all-users",
            headers=get_headers(token),
        )
        response.raise_for_status()

        df = pd.DataFrame(response.json())
        if df.empty or "member_id" not in df.columns:
            return f"{member_id_prefix}0000"

        df["member_id_clean"] = pd.to_numeric(df["member_id"], errors="coerce")

        lower_bound = int(f"{member_id_prefix}0000")
        upper_bound = lower_bound + 10000

        filtered_df = df[
            (df["member_id_clean"] >= lower_bound)
            & (df["member_id_clean"] <= upper_bound)
        ]

        sorted_ids = sorted(
            filtered_df["member_id_clean"].dropna().unique().astype(int)
        )

        if not sorted_ids:
            return str(lower_bound)

        for idx in range(len(sorted_ids) - 1):
            current_id = sorted_ids[idx]
            next_id = sorted_ids[idx + 1]
            if next_id - current_id > 1:
                return str(current_id + 1)

        return str(max(sorted_ids) + 1)


@app.command("next-id", help="Getting the first available ID using a specific prefix.")
def get_next_member_id_command(
    member_id_prefix: str = typer.Argument(
        ..., help="The numerical prefix to filter and search gaps for (e.g. 2)"
    ),
):
    """CLI routing function that Typer safely parses."""
    typer.echo(f"Fetching next available ID for prefix: {member_id_prefix}...")

    next_id = MemberID.get_next_member_id(member_id_prefix=member_id_prefix)

    print(f"[bold green]Next Available ID:[/bold green] {next_id}")


@app.command("validate", help="Check if an existing ID is valid.")
def validate_member_id(member_id: str):
    typer.echo(f"Validating ID: {member_id}")
