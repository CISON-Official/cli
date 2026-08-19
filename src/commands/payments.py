#!/usr/bin/env python3
import typer
import pandas as pd
from requests import Session

from src.utils import get_headers
from src.decorators import api_caller


class Payments:
    @api_caller
    @staticmethod
    def get_users_with_partial_payments(**kwargs) -> pd.DataFrame:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/data/users/partial-payment-latest",
                headers=get_headers(token),
            )

            response.raise_for_status()

            data = pd.read_json(response.json()["data"])
            return data
        except Exception as e:
            raise typer.Exit(1)

    @api_caller
    @staticmethod
    def get_users_without_payments(**kwargs) -> pd.DataFrame:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/data/users/no-payment-latest",
                headers=get_headers(token),
            )

            response.raise_for_status()

            data = pd.read_json(response.json()["data"])
            return data
        except Exception as e:
            raise typer.Exit(1)

    @api_caller
    @staticmethod
    def get_users_with_complete_payments(**kwargs) -> pd.DataFrame:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/data/users/complete-payment-latest",
                headers=get_headers(token),
            )

            response.raise_for_status()

            return response.json()["data"]

        except Exception as e:
            print(e)
            raise typer.Exit(1)
