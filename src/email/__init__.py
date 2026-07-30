#!/usr/bin/env python3

import typer

from src.email.topicid import app as topic_app
from src.email.campaigns import app as campaign_app
from src.email.mailing_list import app as mailinglist_app

app = typer.Typer(name="emails")
app.add_typer(topic_app)
app.add_typer(campaign_app)
app.add_typer(mailinglist_app)