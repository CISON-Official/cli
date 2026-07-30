#!/usr/bin/env python3
"""Campaign reporting and analytics operations for the Zoho Campaigns API."""

from __future__ import annotations

from typing import Any

import requests

from src.config import setting
from src.email.base import EmailBase




class Reports(EmailBase):
    """Fetch engagement reports and statistics for sent campaigns."""

    def opens(self, campaign_key: str, *, from_index: int = 1, range_count: int = 25) -> list[dict[str, Any]]:
        """Fetch the list of recipients who opened a campaign.

        Args:
            campaign_key: The campaign's unique key.
            from_index: 1-based starting index for pagination.
            range_count: Maximum number of records to return.

        Returns:
            A list of open-event dictionaries.

        Raises:
            APIError: If the API call fails.

        Example:
            >>> Reports().opens("9a8b7c6d")  # doctest: +SKIP
            [{'email': 'jane@example.com', 'opened_time': '...'}, ...]
        """
        
        params = {"campaignkey": campaign_key, "fromindex": from_index, "range": range_count}
        response = requests.get("getopendetail", params=params)
        response.get("list_of_details")

    def clicks(self, campaign_key: str, *, from_index: int = 1, range_count: int = 25) -> list[dict[str, Any]]:
        """Fetch the list of recipients who clicked a link in a campaign.

        Args:
            campaign_key: The campaign's unique key.
            from_index: 1-based starting index for pagination.
            range_count: Maximum number of records to return.

        Returns:
            A list of click-event dictionaries.

        Raises:
            APIError: If the API call fails.

        Example:
            >>> Reports().clicks("9a8b7c6d")  # doctest: +SKIP
            [{'email': 'jane@example.com', 'clicked_link': 'https://...'}, ...]
        """
        campaign_key = require_non_empty(campaign_key, field_name="campaign_key")
        params = {"campaignkey": campaign_key, "fromindex": from_index, "range": range_count}
        response = self.get("getclickdetail", params=params)
        return list(response.get("list_of_details", []))

    def bounces(
        self,
        campaign_key: str,
        *,
        bounce_type: str = "all",
        from_index: int = 1,
        range_count: int = 25,
    ) -> list[dict[str, Any]]:
        """Fetch bounced email records for a campaign.

        Args:
            campaign_key: The campaign's unique key.
            bounce_type: One of ``"all"``, ``"hard"``, or ``"soft"``.
            from_index: 1-based starting index for pagination.
            range_count: Maximum number of records to return.

        Returns:
            A list of bounce-event dictionaries.

        Raises:
            APIError: If the API call fails.

        Example:
            >>> Reports().bounces("9a8b7c6d", bounce_type="hard")  # doctest: +SKIP
            [{'email': 'bad@example.com', 'bounce_type': 'hard'}, ...]
        """
        campaign_key = require_non_empty(campaign_key, field_name="campaign_key")
        params = {
            "campaignkey": campaign_key,
            "bouncetype": bounce_type,
            "fromindex": from_index,
            "range": range_count,
        }
        response = self.get("getbouncedetail", params=params)
        return list(response.get("list_of_details", []))

    def unsubscribes(
        self, campaign_key: str, *, from_index: int = 1, range_count: int = 25
    ) -> list[dict[str, Any]]:
        """Fetch the list of recipients who unsubscribed after a campaign.

        Args:
            campaign_key: The campaign's unique key.
            from_index: 1-based starting index for pagination.
            range_count: Maximum number of records to return.

        Returns:
            A list of unsubscribe-event dictionaries.

        Raises:
            APIError: If the API call fails.

        Example:
            >>> Reports().unsubscribes("9a8b7c6d")  # doctest: +SKIP
            [{'email': 'jane@example.com', 'unsub_time': '...'}, ...]
        """
        campaign_key = require_non_empty(campaign_key, field_name="campaign_key")
        params = {"campaignkey": campaign_key, "fromindex": from_index, "range": range_count}
        response = self.get("getunsubscribedetail", params=params)
        return list(response.get("list_of_details", []))

    def spam_complaints(
        self, campaign_key: str, *, from_index: int = 1, range_count: int = 25
    ) -> list[dict[str, Any]]:
        """Fetch spam complaint records for a campaign.

        Args:
            campaign_key: The campaign's unique key.
            from_index: 1-based starting index for pagination.
            range_count: Maximum number of records to return.

        Returns:
            A list of spam-complaint dictionaries.

        Raises:
            APIError: If the API call fails.

        Example:
            >>> Reports().spam_complaints("9a8b7c6d")  # doctest: +SKIP
            [{'email': 'jane@example.com', 'complaint_time': '...'}, ...]
        """
        campaign_key = require_non_empty(campaign_key, field_name="campaign_key")
        params = {"campaignkey": campaign_key, "fromindex": from_index, "range": range_count}
        response = self.get("getspamdetail", params=params)
        return list(response.get("list_of_details", []))

    def campaign_statistics(self, campaign_key: str) -> dict[str, Any]:
        """Fetch aggregate summary statistics for a campaign.

        Args:
            campaign_key: The campaign's unique key.

        Returns:
            A dictionary of aggregate metrics (e.g. sent, opens, clicks,
            bounces, unsubscribes counts and rates).

        Raises:
            APIError: If the API call fails.

        Example:
            >>> Reports().campaign_statistics("9a8b7c6d")  # doctest: +SKIP
            {'sent': 1000, 'opens': 320, 'clicks': 88, 'bounces': 12}
        """
        campaign_key = require_non_empty(campaign_key, field_name="campaign_key")
        response = self.get("getcampaignreportsummary", params={"campaignkey": campaign_key})
        return dict(response.get("summary", response))
