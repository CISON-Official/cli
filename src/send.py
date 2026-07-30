#!/usr/bin/env python3

import os
import asyncio
import logging
from time import sleep
from datetime import datetime
from dataclasses import asdict

import typer
from jinja2 import Template

from src.config import setting

# from src.loader import GlobalLoader
from src.commands.payments import Payments
from src.email.campaigns import EmailCampaign
from src.types import Payments as PType, Paid
from src.email.mailing_list import MailingList
from src.__cloudflare import (
    upload_template_to_server,
    enable_subdomain,
    disable_subdomain,
    wait_until_accessible,
)

logger = logging.getLogger("notification")

app = typer.Typer(name="notification", help="command section for sending emails")

TITLE_MAP = {
    "annual_dues_2026": "2026 Annual Dues",
    "dev_levy_2026": "2026 Development Levy",
    "nsa_dues": "NSA Dues",
    "annual_dues_2025": "2025 Annual Dues",
    "dev_levy_2025": "2025 Development Levy",
    "annual_dues_2024": "2024 Annual Dues",
    "dev_levy_2024": "2024 Development Levy",
    "new_member_fee": "New Member Fee",
    "transition_fee": "Transition Fee",
}


def format_fee_list(fees: list):
    formatted = [TITLE_MAP[key] for key in fees]
    return formatted


def generate_html(dict_data):
    with open(
        "src/templates/cison_no_payment_template.html", "r", encoding="utf-8"
    ) as f:
        html_content = f.read()

    template = Template(html_content)
    rendered_html = template.render(**dict_data)
    return rendered_html


@app.command(name="payment")
def send_payment_notification(
    ctx: typer.Context,
    paymentstatus: bool = typer.Option(
        default=False,
        help="True indicates using users without any payment while false indicates using users with incomplete payment",
    ),
):
    loader = ctx.obj

    # with loader.capture_output() as _:
    asyncio.run(enable_subdomain())
    # sleep(150)

    if not wait_until_accessible(
        f"http://{setting.CLOUDFLARE_SUBDOMAIN}.{setting.CLOUDFLARE_MAIN_DOMAIN}",
        interval=5,
        max_attempts=12,
    ):
        logger.info("Unable to access server...\nShutting down operations...")
        typer.Exit(1)

    logger.info("waiting for subdomain to propagate...")

    users = PType(
        user_id=123,
        member_id="1234",
        first_name="Dilibe",
        last_name="Fidelugwuowo",
        middle_name="Franklin",
        certificate_name="Fidelugwuowo Dilibe Franklin",
        phone_number="123456789",
        user_email=str(setting.ADMIN_EMAIL),
        fees=Paid(
            new_member_fee=True,
            annual_dues_2024=True,
            dev_levy_2024=True,
            annual_dues_2025=True,
            dev_levy_2025=True,
            annual_dues_2026=False,
            dev_levy_2026=False,
        ),
    )

    root_dir = "room"
    os.makedirs(root_dir, exist_ok=True)
    fees = []
    for key, value in asdict(users.fees).items():
        if not (value) and value is not None:
            fees.append(key)

    html = generate_html(dict(fees=format_fee_list(fees), first_name=users.first_name))
    logger.info("HTML generated..")
    file_name = (
        f"{users.first_name}{str(datetime.now().timestamp()).replace(".", "")}.html"
    )

    with open(f"{root_dir}/{file_name}", "w") as file:
        file.write(html)

    logger.info("running subprocess...")

    upload_template_to_server(f"{root_dir}/{file_name}")

    public_url = f"http://{setting.CLOUDFLARE_SUBDOMAIN}.{setting.CLOUDFLARE_MAIN_DOMAIN}/{file_name}"

    mailinglist = MailingList()
    first = mailinglist.create_mailing_list(
        emailids=[users.user_email],
        listname=f"mailinglist {datetime.now().timestamp()}",
        signupform="public",
        listdescription=f"Mailing List for Payment Notification for {datetime.now().timestamp()}",
    )

    if not first:
        logger.info("Error while creating mailing list")

    print(f"List ID is {first}")
    campaign = EmailCampaign()
    campaign_key = campaign.create_campaign(
        f"Payment Remainder {datetime.now().timestamp()}",
        "CISON | Overdue Payment Notice",
        list_details=[first],  # type: ignore
        content_url=public_url,
    )

    if not campaign_key:
        logger.info("Error while creating campaign...")

    if campaign.send_campaign(campaignkey=campaign_key):  # type: ignore
        logger.info("Campaign has been sent")
    else:
        logger.info("Unable to send campaign...")

    # with loader.capture_output() as _:
    # asyncio.run(disable_subdomain())


# @app.command(name="conference", help="Command to send conference remainder")
# def send_conference_remainder
