#!/usr/bin/env python3

import os
import asyncio
import logging
from time import sleep
from pdb import set_trace
from typing import Iterable
from datetime import datetime
from dataclasses import asdict

import tqdm
import typer
import pandas as pd
from jinja2 import Template

# from src.loader import GlobalLoader
from src.config import setting
from src.commands.payments import Payments
from src.fixtures import users as fixUsers
from src.email.campaigns import EmailCampaign
from src.types import Payments as PType, Paid
from src.email.mailing_list import MailingList
from src.commands.user import User
from src.utils import (
    create_disk_cached_function,
    suppress_output,
    find_sub_combinations,
)
from src.email.utils import wait_until_mailingkey_accessible
from src.__cloudflare import upload_template_to_server, wait_until_accessible

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


@app.command(name="zero-payment")
def send_payment_notification(
    ctx: typer.Context,
    paymentstatus: bool = typer.Option(
        default=False,
        help="True indicates using users without any payment while false indicates using users with incomplete payment",
    ),
):

    if not wait_until_accessible(
        f"http://{setting.CLOUDFLARE_SUBDOMAIN}.{setting.CLOUDFLARE_MAIN_DOMAIN}",
        interval=5,
        max_attempts=12,
    ):
        logger.info("Unable to access server...\nShutting down operations...")
        typer.Exit(1)

    logger.info("waiting for subdomain to propagate...")
    users = fixUsers
    root_dir = "room"
    os.makedirs(root_dir, exist_ok=True)
    fees = []
    for key, value in asdict(users[0].fees).items():
        if not (value) and value is not None:
            fees.append(key)

    html = generate_html(dict(fees=format_fee_list(fees)))
    logger.info("HTML generated..")
    file_name = (
        f"outstanding_payments{str(datetime.now().timestamp()).replace(".", "")}.html"
    )

    with open(f"{root_dir}/{file_name}", "w") as file:
        file.write(html)

    logger.info("running subprocess...")

    upload_template_to_server(f"{root_dir}/{file_name}")

    public_url = f"http://{setting.CLOUDFLARE_SUBDOMAIN}.{setting.CLOUDFLARE_MAIN_DOMAIN}/{file_name}"

    mailinglist = MailingList()
    first = mailinglist.create_mailing_list(
        emailids=[i.user_email for i in users],
        listname=f"mailinglist {datetime.now().timestamp()}",
        signupform="public",
        listdescription=f"Mailing List for Payment Notification for {datetime.now().timestamp()}",
    )

    if not first:
        logger.info("Error while creating mailing list")
        typer.Exit()

    for user in users:
        mailinglist.add_contacts_existing_list(str(first), [user.user_email])
        mailinglist.subscribe(
            str(first),
            user.user_email,
            firstname=user.first_name,
            lastname=user.last_name,
        )

    print(f"List ID is {first}")
    campaign = EmailCampaign()
    campaign_key = campaign.create_campaign(
        f"Payment Remainder {datetime.now().timestamp()}",
        "CISON | Overdue Payment Notice",
        list_details=[str(first)],
        content_url=public_url,
    )

    if not campaign_key:
        logger.info("Error while creating campaign...")

    if campaign.send_campaign(campaignkey=campaign_key, list_details=[first]):  # type: ignore
        logger.info("Campaign has been sent")
    else:
        logger.info("Unable to send campaign...")

    # with loader.capture_output() as _:
    # asyncio.run(disable_subdomain())


@app.command(name="partial-payment")
def send_payment_notification_for_zero_payment():

    def filter_sub_function(single: PType, combine: tuple[str]) -> bool:
        fees = single.fees.to_dict()
        combine_set = set(combine)

        for key, value in fees.items():
            if key in combine_set:
                if not value:
                    return False
            else:
                if value:
                    return False

        return True

    users = create_disk_cached_function(
        User.all_users_with_partial_payment, cache_directory="partial_payment"
    )
    partial_payment = users()

    combinations = find_sub_combinations(partial_payment["data"])
    custom_users = list(map(PType.from_dict, partial_payment["data"]))

    user_active_fees = [
        (user, {k for k, v in user.fees.to_dict().items() if v})
        for user in custom_users
    ]

    for i in combinations:
        combine_set = set(i)

        correct_users = [
            user for user, active_fees in user_active_fees if active_fees == combine_set
        ]
        if len(correct_users) <= 0:
            continue
        if len(correct_users) <= 9:
            correct_users.extend(fixUsers)

        print(f"{', '.join(i)} {len(correct_users)}")

        root_dir = "room"
        os.makedirs(root_dir, exist_ok=True)
        fees = []
        for key, value in asdict(correct_users[0].fees).items():
            if not (value) and value is not None:
                fees.append(key)

        html = generate_html(dict(fees=format_fee_list(fees)))
        logger.info("HTML generated..")
        file_name = f"outstanding_payments{str(datetime.now().timestamp()).replace(".", "")}.html"

        with open(f"{root_dir}/{file_name}", "w") as file:
            file.write(html)

        logger.info("running subprocess...")

        upload_template_to_server(f"{root_dir}/{file_name}")

        public_url = f"http://{setting.CLOUDFLARE_SUBDOMAIN}.{setting.CLOUDFLARE_MAIN_DOMAIN}/{file_name}"
        count = len(correct_users) // int(setting.MAILINGLIST_LIMIT)
        for j in range(0, count + 1):
            segment_user = correct_users[j : (j + 1) * int(setting.MAILINGLIST_LIMIT)]
            mailing=MailingList()
            mailinglist = mailing.create_mailing_list(
                emailids=[w.user_email for w in segment_user[:10]],
                listname=f"mailinglist {datetime.now().timestamp()}".replace(
                    ",", ""
                ).replace(".", ""),
                signupform="public",
                listdescription=f"Mailing List for Payment Notification for {datetime.now().timestamp()}",
            )
            with suppress_output():
                for batch in range(0, len(segment_user), 10):
                    batch_list = segment_user[batch : batch + 10]
                    MailingList().add_contacts_existing_list(
                        emailids=[t.user_email for t in batch_list],
                        listkey=str(mailinglist),
                    )
                    [
                        MailingList().subscribe(
                            contact_email=t.user_email,
                            firstname=t.first_name,
                            lastname=t.last_name,
                            listkey=str(mailinglist),
                        )
                        for t in batch_list
                    ]
                campaignkey = EmailCampaign().create_campaign(
                    campaign_name=f"Partial Payment Campaign {datetime.now().isoformat()}",
                    subject="CISON | Overdue Payment Notice",
                    list_details=[str(mailinglist)],
                    content_url=public_url,
                )

            if campaignkey:
                status = EmailCampaign().send_campaign(
                    campaignkey=campaignkey, list_details=[str(mailinglist)]
                )

            MailingList().delete_mailing_list(
                listkey=str(mailinglist), deletecontact="on"
            )


@app.command(name="conference", help="Command to send conference remainder")
def send_conference_remainder(
    mailing: str = typer.Option(
        help="Mailing list as an optional argument", default=None
    ),
    campkey: str = typer.Option(
        help="Campaign Key for organizing the competition", default=None
    ),
):
    try:
        with open(
            "src/templates/ConferenceInvitation.html", "r", encoding="utf-8"
        ) as f:
            html_content = f.read()

        template = Template(html_content)
        rendered_html = template.render()

        file_name = f"conference_reminder-{str(datetime.now().timestamp()).replace(".", "").replace(" ", "_")}.html"

        with open(f"room/{file_name}", "w") as file:
            file.write(rendered_html)

        upload_template_to_server(f"room/{file_name}")

        public_url = f"http://{setting.CLOUDFLARE_SUBDOMAIN}.{setting.CLOUDFLARE_MAIN_DOMAIN}/{file_name}"
        logger.info(f"Created the public url: {public_url}")

        if not wait_until_accessible(public_url):
            logger.debug("Unable to connect to public URL")
            raise ConnectionRefusedError("Unable to access campaign template")

        campaign = EmailCampaign()

        get_cached_user_info = create_disk_cached_function(
            User.get_all_users, cache_directory=".cache"
        )
        logger.info("Retriving users")
        response = get_cached_user_info()
        # set_trace()
        (
            data,
            batch_size,
            mailinglist,
        ) = (
            User.rename_columns(pd.DataFrame(response)),
            9,
            MailingList(),
        )

        # print(data.head())

        count = len(data.user_email) // int(setting.MAILINGLIST_LIMIT)
        if count > 0:
            logger.info(
                f"Length of data '{len(data.user_email)}' allowed {setting.MAILINGLIST_LIMIT}."
            )
            logger.info(f"Splitting the data into '{count}' parts")

        for key in range(0, count + 1):
            if not mailing:
                logger.info("Creating mailing list")
                first = mailinglist.create_mailing_list(
                    emailids=[str(setting.EMAIL_ADMIN)],
                    listname=f"Conference {datetime.now().timestamp()}",
                    signupform="public",
                    listdescription=f"Mailing List for Payment Notification for {datetime.now().timestamp()}",
                )
            else:
                first = mailing
            wait_until_mailingkey_accessible(first)  # type: ignore
            if not first:
                logger.debug("Error while creating mailing list")
            for i in tqdm.tqdm(
                range(
                    key * int(setting.MAILINGLIST_LIMIT),
                    (key + 1) * int(setting.MAILINGLIST_LIMIT),
                    batch_size,
                )
            ):
                if i > len(data.user_email):
                    break
                batch = data.user_email[i : i + batch_size].to_list()
                # print(batch)
                with suppress_output():
                    mailinglist.add_contacts_existing_list(str(first), batch)  # type: ignore
                batch_pd = data.iloc[i : i + batch_size]

                for _, w in tqdm.tqdm(batch_pd.iterrows(), total=len(batch_pd)):
                    with suppress_output():
                        mailinglist.subscribe(
                            first,  # type: ignore
                            w.user_email,  # type: ignore
                            firstname=w.first_name,  # type: ignore
                            lastname=w.last_name,
                        )
            #       batch = data.loc[i]

            #     mailinglist.subscribe(
            #         first,  # type: ignore
            #         batch.user_email,  # type: ignore
            #         firstname=batch.display_name,  # # type: ignore
            #     )

            if not campkey:
                with suppress_output():
                    campaign_key = campaign.create_campaign(
                        f"Conference Remainder {datetime.now().timestamp()}",
                        "CISON | 50th Annivasary Conference Notice",
                        list_details=[first],  # type: ignore
                        content_url=public_url,
                    )
            else:
                campaign_key = campkey

            if not campaign_key:
                logger.info("Error while creating campaign...")

            if campaign.send_campaign(campaignkey=campaign_key):  # type: ignore
                logger.info("Campaign has been sent")
            else:
                logger.info("Unable to send campaign...")

    except Exception as e:
        print(e)
