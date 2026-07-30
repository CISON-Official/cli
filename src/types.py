#!/usr/bin/env python3

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
