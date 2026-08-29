"""
Transaction Management CLI Module.

This module provides the Command Line Interface (CLI) commands and underlying
API clients to query, fetch, and format transaction log data from the core system.
It utilizes Typer for CLI parsing and Requests for HTTP infrastructure.
"""

import ast
import pdb
import asyncio
from typing import Literal, Optional
from datetime import datetime, timedelta

import typer
import pandas as pd
from requests import Session
from requests.exceptions import HTTPError

from src.utils import get_headers
from src.types import OutputFormat
from src.utils import save_dataframe
from src.decorators import api_caller
from src.gui.print import print_error_panel

app = typer.Typer(name="transaction")


class Transactions:
    """
    Core API client operations handling transaction database queries.

    Acts as the bridge between raw CLI commands and the backend REST API.
    """

    @api_caller
    @staticmethod
    def get_transactions(
        startdate: datetime = datetime.now() - timedelta(days=28),
        enddate: datetime = datetime.now(),
        per_page: int = 100,
        page: int = 1,
        *args,
        **kwargs,
    ) -> dict:
        """
        Executes a GET request against the remote API to fetch filtered transaction records.

        Args:
            startdate (datetime): Lower boundary for the transaction timestamp query.
            enddate (datetime): Upper boundary for the transaction timestamp query.
            per_page (int): Pagination ceiling restricting how many records return per request.
            page (int): Current target pagination index offset.
            *args: Variable length argument list caught for decorator handling.
            **kwargs: Dynamic keyword arguments contextually injected by the `@api_caller`
                decorator (expects keys: 'session', 'token', 'root_url').

        Returns:
            dict: The parsed JSON payload containing transaction objects if successful,
                or an empty dictionary if the request fails or raises an HTTP error.

        Raises:
            HTTPError: Handled internally; outputs a visual panel alert via print_error_panel.
        """
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            arguments = dict(
                # startdate=startdate.strftime("%d/%m/%y %H:%M:%S"),
                # enddate=enddate.strftime("%d/%m/%y %H:%M:%S"),
                # status="complete",
                per_page=per_page,
                page=page,
            )

            response = session.get(
                f"{root_url.rstrip('/')}/transactions",
                headers=get_headers(token),
                json=arguments,
            )

            response.raise_for_status()

            return response.json()

        except HTTPError as e:
            print_error_panel(f"Error generated while trying to transaction data: {e}")
            return {}


@app.command(name="get")
def get_transactions_command(
    startdate: datetime = typer.Option(
        default=None,
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"],
        help="Start date for transactions query (e.g., 2026-01-31).",
    ),
    enddate: datetime = typer.Option(
        default=None,
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"],
        help="End date for transactions query (e.g., 2026-01-31T23:59:59).",
    ),
    per_page: int = typer.Option(
        100, help="Number of items per page index collection."
    ),
    page: int = typer.Option(1, help="Page number to retrieve sequentially."),
):
    """
    Retrieve transaction logs within a specific date range.

    Executes a paginated lookup. If no explicit time filters are provided via options,
    the system defaults down to querying historical records over the last 28 days.
    """

    if startdate is None:
        startdate = datetime.now() - timedelta(days=28)
    if enddate is None:
        enddate = datetime.now()

    result = Transactions.get_transactions(
        startdate=startdate, enddate=enddate, per_page=per_page, page=page
    )

    if result:
        # typer.echo(result)
        save_dataframe(
            data=result["transactions"],
            filename=f"complete_transactions_{page}_{per_page}.csv",
            default_name="complete-transaction",
            output_format=OutputFormat.csv,
        )


@app.command(
    name="ptppc",
    help="Command to return a file filled with people that paid for either preconference or conference or both",
)
def get_people_that_paid_for_preconference_and_conference(
    x: int,
    transaction_type: Optional[Literal["preconference", "conference"]] = typer.Option(
        default=None,
        help="None implies that you'd want all of them, while listing any of their names, implies that you want a single of them",
    ),
):
    def _sync_conference(range_num: int):
        try:
            return Transactions.get_transactions(per_page=500, page=range_num)[
                "transactions"
            ]
        except Exception:
            return None

    def has_product_id(line_items_str, target_id):
        """Checks if a target product_id exists within the line_items list."""
        try:
            items = (
                ast.literal_eval(line_items_str)
                if isinstance(line_items_str, str)
                else line_items_str
            )
            if isinstance(items, list):
                return any(int(item.get("product_id")) in target_id for item in items)
        except Exception:
            pass
        return False

    def _cleanup(df_only: pd.DataFrame):
        all_data = []
        for _, row in df_only.iterrows():
            data = {}
            billing = (
                ast.literal_eval(row.billing)
                if isinstance(row.billing, str)
                else row.billing
            )
            data["name"] = billing["full_name"]
            data["email"] = billing["email"]
            data["phone"] = billing["phone"]
            if isinstance(row.line_items, str):
                items = row.line_items
            else:
                items = ast.literal_eval(str(row.line_items))
            products = [
                i["name"] for i in items if int(i["product_id"]) in available_product_id
            ]
            amount = sum(
                [
                    float(i["subtotal"])
                    for i in items
                    if int(i["product_id"]) in available_product_id
                ]
            )

            data["products"] = products
            data["amount"] = amount

            all_data.append(data)
        return all_data

    async def main():
        tasks = [asyncio.to_thread(_sync_conference, i) for i in range(x)]
        return await asyncio.gather(*tasks)

    raw_results = asyncio.run(main())

    data = [pd.DataFrame(res) for res in raw_results if res]

    df = pd.concat(data, axis=0)
    # pdb.set_trace()
    print(df.head())
    df = df[df["status"] == "completed"]
    df["line_items"] = df["line_items"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    if transaction_type == "conference":
        available_product_id = [12817, 12818, 14270, 14271]
        file_name = "Conference.csv"
    elif transaction_type == "preconference":
        available_product_id = [12816, 14302]
        file_name = "preconference.csv"
    else:
        available_product_id = [12817, 12818, 14270, 14271, 12816, 14302]
        file_name = "preconference_and_conference.csv"

    only_df = df[
        df["line_items"].apply(lambda x: has_product_id(x, available_product_id))
    ]
    cleaned_data = _cleanup(only_df)

    pd.DataFrame(cleaned_data).to_csv(file_name)
