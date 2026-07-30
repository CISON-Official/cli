#!/usr/bin/env python3
import requests

from src.config import setting


def get_access_token():
    url = f"https://accounts.zoho.com/oauth/v2/token"

    params = {
        "refresh_token": setting.REFRESH_TOKEN,
        "client_id": setting.CLIENT_ID,
        "client_secret": setting.CLIENT_SECRET,
        "grant_type": "refresh_token",
    }

    response = requests.post(url, params=params)
    response.raise_for_status()

    return response.json()["access_token"]


def get_email_header(token: str) -> dict:

    return {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
