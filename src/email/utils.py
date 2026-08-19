#!/usr/bin/env python3
from time import sleep

from src.email.mailing_list import MailingList


def wait_until_mailingkey_accessible(listkey: str) -> None:

    # sleep(30)
    print(f"Wating for mailing listing key to be accessible...")
    mailinglist = MailingList()

    while True:
        if mailinglist.get_mailing_list(listkey):
            break
