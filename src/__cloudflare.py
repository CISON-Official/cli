#!/usr/bin/env python3
import time
import logging

import typer
import requests
from cloudflare import AsyncCloudflare
from cloudflare.types.dns.record_list_params import Name

from src.config import setting

TOKEN = str(setting.CLOUDFLARE_API_TOKEN)
ZONE_ID = str(setting.CLOUDFLARE_ZONE_ID)


client = AsyncCloudflare(api_token=TOKEN)
logger = logging.getLogger("cloudflare")


async def get_subdomain_record():
    """Finds an existing DNS record for a subdomain."""
    try:
        subdomain_name = str(setting.CLOUDFLARE_SUBDOMAIN)
        name = Name(
            contains=str(setting.CLOUDFLARE_MAIN_DOMAIN), startswith=subdomain_name
        )
        records = await client.dns.records.list(zone_id=ZONE_ID, name=name)

        async for record in records:
            if record.name == f"{subdomain_name}.{setting.CLOUDFLARE_MAIN_DOMAIN}":
                return record
        return None
    except Exception as e:
        logger.error(f"Error fetching record: {e}")
        return None


async def enable_subdomain(proxied: bool = False):
    """
    Enables a subdomain by creating or updating its DNS record.

    :Note:
    After a subdomain is enabled, ensure that you wait at least 3 minutes.This is to enable the domain name circulate over the available and close DNS server.
    """
    subdomain_name = str(setting.CLOUDFLARE_SUBDOMAIN)
    target_ip = str(setting.CLOUDFLARE_IP_ADDRESS)
    record = await get_subdomain_record()

    if record:
        logger.info(
            f"Subdomain {subdomain_name} already exists (ID: {record.id}). Updating..."
        )
        # updated_record = await client.dns.records.update(
        #     dns_record_id=record.id,
        #     zone_id=ZONE_ID,
        #     content=target_ip,
        #     name=subdomain_name,
        #     type="A",
        #     proxied=proxied,
        #     ttl=1,
        # )  # type: ignore
        # print(f"Successfully updated: {updated_record.name}")  # type: ignore
    else:
        print(f"Creating new subdomain: {subdomain_name}")
        # Create new record
        new_record = await client.dns.records.create(
            zone_id=ZONE_ID,
            content=target_ip,
            name=subdomain_name,
            type="A",
            proxied=proxied,
            ttl=1,
        )  # type: ignore
        print(f"Successfully created: {new_record.name}")  # type: ignore
        logger.info("Waiting for ")
        time.sleep(600)


async def disable_subdomain():
    """Disables a subdomain by deleting its DNS record."""
    subdomain_name = str(setting.CLOUDFLARE_SUBDOMAIN)
    record = await get_subdomain_record()

    if not record:
        print(f"Subdomain {subdomain_name} does not exist or is already disabled.")
        return

    print(f"Disabling {subdomain_name} by deleting record ID: {record.id}")
    await client.dns.records.delete(dns_record_id=record.id, zone_id=ZONE_ID)
    print(f"Successfully disabled {subdomain_name}.")


def upload_template_to_server(file_to_upload: str):

    url_with_key = f"http://{setting.CLOUDFLARE_SUBDOMAIN}.{setting.CLOUDFLARE_MAIN_DOMAIN}?key={setting.UPLOAD_ID}"

    try:
        with open(file_to_upload, "rb") as f:
            files = {"html_file": (file_to_upload, f, "text/html")}

            data = {"upload": "1"}

            print(f"Sending POST request to {setting.CLOUDFLARE_MAIN_DOMAIN}...")

            response = requests.post(url_with_key, files=files, data=data)

            if response.status_code == 200:
                print("Request completed successfully!")
                # print("\nServer Response snippet:")
                # print(response.text[-500:])
            else:
                print(f"Failed! Server returned status code: {response.status_code}")
                if response.status_code == 403:
                    print("Likely cause: Incorrect SECRET_KEY or blocked by .htaccess.")

    except FileNotFoundError:
        print(
            f"Error: The local file '{setting.CLOUDFLARE_SUBDOMAIN}.{setting.CLOUDFLARE_MAIN_DOMAIN}' was not found."
        )
    except requests.exceptions.ConnectionError:
        print(f"Unable to connect with {url_with_key}")
    except Exception as e:
        print(f"An error occurred: {e}")
        typer.Exit(1)


def wait_until_accessible(
    url: str, interval: int = 5, timeout: int = 5, max_attempts: int | None = None
) -> bool:
    """
    Pings a URL every `interval` seconds until it returns an HTTP 2xx status code.

    :param url: The target HTTP/HTTPS URL to ping.
    :param interval: Seconds to wait between retries (default: 5s).
    :param timeout: Connection timeout per request (default: 5s).
    :param max_attempts: Max retry count. Pass None for infinite retries.
    :return: True when accessible, False if max_attempts exceeded.
    """
    attempts = 0

    print(f"🔄 Waiting for {url} to become accessible...")

    while True:
        attempts += 1
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 405:
                response = requests.get(url, timeout=timeout, stream=True)

            if response.ok or response.status_code == 403:
                print(f"✅ {url} is live! (Status Code: {response.status_code})")
                return True
            else:
                print(
                    f"⏳ [{attempts}] Returned HTTP {response.status_code}. Retrying in {interval}s..."
                )

        except requests.RequestException as e:
            print(
                f"⏳ [{attempts}] Host unreachable ({type(e).__name__}). Retrying in {interval}s..."
            )

        if max_attempts and attempts >= max_attempts:
            print(f"❌ Reached max attempts ({max_attempts}). Stopping ping.")
            return False

        time.sleep(interval)
