#!/usr/bin/env python3
from enum import Enum
from typing import Optional
from dataclasses import dataclass


@dataclass
class Payments:

    user_id: int
    member_id: str
    first_name: str
    middle_name: str
    last_name: str
    phone_number: str
    certificate_name: str
    user_email: str
    fees: Paid

    @staticmethod
    def from_dict(
        data: dict[str, str | dict[str, str | dict[str, str | bool]]],
    ) -> Payments:
        return Payments(
            user_id=int(data.get("user_id")),  # type: ignore
            member_id=data.get("member_id"),  # type: ignore
            first_name=data.get("first_name"),  # type: ignore
            middle_name=data.get("middle_name"),  # type: ignore
            last_name=data.get("last_name"),  # type: ignore
            phone_number=data.get("phone_number"),  # type: ignore
            certificate_name=data.get("certificate_name"),  # type: ignore
            user_email=data.get("user_email"),  # type: ignore
            fees=Paid.from_dict(data.get("fees")),  # type: ignore
        )


@dataclass
class Paid:
    annual_dues_2026: Optional[bool] = None
    dev_levy_2026: Optional[bool] = None
    nsa_dues: Optional[bool] = None
    annual_dues_2025: Optional[bool] = None
    dev_levy_2025: Optional[bool] = None
    annual_dues_2024: Optional[bool] = None
    dev_levy_2024: Optional[bool] = None
    new_member_fee: Optional[bool] = None
    transition_fee: Optional[bool] = None

    @staticmethod
    def from_dict(data: dict[str, str | bool]) -> Paid:
        data = data["paid"]  # type: ignore
        return Paid(
            annual_dues_2026=data.get("annual_dues_2026"),  # type: ignore
            dev_levy_2026=data.get("dev_levy_2026"),  # type: ignore
            nsa_dues=data.get("nsa_dues"),  # type: ignore
            annual_dues_2025=data.get("annual_dues_2025"),  # type: ignore
            dev_levy_2025=data.get("dev_levy_2025"),  # type: ignore
            annual_dues_2024=data.get("annual_dues_2024"),  # type: ignore
            dev_levy_2024=data.get("dev_levy_2024"),  # type: ignore
            new_member_fee=data.get("new_member_fee"),  # type: ignore
            transition_fee=data.get("transition_fee"),  # type: ignore
        )

    def to_dict(self) -> dict[str, Optional[bool]]:
        return dict(
            annual_dues_2026=self.annual_dues_2026,
            dev_levy_2026=self.dev_levy_2026,
            nsa_dues=self.nsa_dues,
            annual_dues_2025=self.annual_dues_2025,
            dev_levy_2025=self.dev_levy_2025,
            annual_dues_2024=self.annual_dues_2024,
            dev_levy_2024=self.dev_levy_2024,
            new_member_fee=self.new_member_fee,
            transition_fee=self.transition_fee,
        )


class OutputFormat(str, Enum):
    csv = "csv"
    json = "json"
    xlsx = "xlsx"
    parquet = "parquet"