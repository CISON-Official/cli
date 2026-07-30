#!/usr/bin/env python3

"""Topic operations for the Zoho Campaigns API."""

from typing import Optional

import typer
import requests

import questionary
from rich.console import Console
from rich.table import Table

from src.config import setting
from src.email.base import EmailBase
from src.exception import handle_error
from src.gui.print import print_error_panel, print_success_panel

app = typer.Typer(
    name="topic",
    help="Get topics, get products, and create topics for Zoho Campaigns.",
)

console = Console()


def display_topics(data: dict) -> None:
    table = Table(title="Topics")
    table.add_column("Topic ID", style="cyan")
    table.add_column("Topic Name", style="green")
    table.add_column("Primary List", style="magenta")

    for topic in data.get("topicDetails", []):
        table.add_row(
            str(topic.get("topicId", "")),
            str(topic.get("topicName", "")),
            str(topic.get("primaryList", "")),
        )

    console.print(table)


def display_products(data: dict) -> None:
    table = Table(title="Products")
    table.add_column("Product ID", style="cyan")
    table.add_column("Product Name", style="green")

    products = data.get("productDetails", data.get("products", []))
    for product in products:
        table.add_row(
            str(product.get("productId", product.get("product_id", ""))),
            str(product.get("productName", product.get("product_name", ""))),
        )

    console.print(table)


class EmailTopic(EmailBase):

    def get_topics(
        self,
        from_index: Optional[int] = None,
        range: Optional[int] = None,
    ) -> list:
        try:
            details = {}
            if from_index is not None:
                details["from_index"] = from_index
            if range is not None:
                details["range"] = range

            if details:
                self.params["details"] = (
                    "{"
                    + ",".join(f"{k}:{v}" for k, v in details.items())
                    + "}"
                )

            response = requests.get(
                f"{setting.EMAIL_API_BASE}/topics",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            handle_error(data)
            display_topics(data)
            return []
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting topics")
            return []
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return []

    def get_products(
        self,
        from_index: Optional[int] = None,
        range: Optional[int] = None,
    ) -> list:
        try:
            details = {}
            if from_index is not None:
                details["from_index"] = from_index
            if range is not None:
                details["range"] = range

            if details:
                self.params["details"] = (
                    "{"
                    + ",".join(f"{k}:{v}" for k, v in details.items())
                    + "}"
                )

            response = requests.get(
                f"{setting.EMAIL_API_BASE}/topics/products",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            handle_error(data)
            display_products(data)
            return []
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting products")
            return []
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return []

    def create_topic(
        self,
        topic_name: str,
        topic_desc: str,
        product_id: Optional[str] = None,
    ) -> None:
        try:
            details = {
                "topic_name": topic_name,
                "topic_desc": topic_desc,
            }
            if product_id:
                details["product_id"] = product_id

            self.params["details"] = (
                "{" + ",".join(f"{k}:{v}" for k, v in details.items()) + "}"
            )

            response = requests.post(
                f"{setting.EMAIL_API_BASE}/topics",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            print(data)
            handle_error(data)
            print_success_panel(
                f"Successfully created topic with ID: {data.get('topic_id')}"
            )
            return
        except requests.exceptions.HTTPError as e:
            print_error_panel(f"Error while creating topic {e}")
            return
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return


@app.command("get-topics")
def get_topics(
    from_index: Optional[int] = typer.Option(None, "--from-index"),
    range: Optional[int] = typer.Option(None, "--range"),
) -> None:
    topic = EmailTopic()
    topic.get_topics(from_index=from_index, range=range)


@app.command("get-products")
def get_products(
    from_index: Optional[int] = typer.Option(None, "--from-index"),
    range: Optional[int] = typer.Option(None, "--range"),
) -> None:
    topic = EmailTopic()
    topic.get_products(from_index=from_index, range=range)


@app.command("create")
def create_topic() -> None:
    topic = EmailTopic()

    topic_name = questionary.text(
        "What is the name of the topic you want to create?"
    ).ask()
    topic_desc = questionary.text(
        "Enter a description for this topic:"
    ).ask()

    is_brand_product = questionary.confirm(
        "Is this a brand product topic? (requires a Product ID)",
        default=False,
    ).ask()

    product_id: Optional[str] = None
    if is_brand_product:
        product_id = questionary.text(
            "Enter the Product ID for this topic:"
        ).ask()

    topic.create_topic(
        topic_name=topic_name, topic_desc=topic_desc, product_id=product_id
    )