#!/usr/bin/env python3

from typing import Optional

import tqdm
import typer
import pandas as pd
from rich import print
from requests import Session
from requests.exceptions import HTTPError

from src.utils import get_headers
from src.decorators import api_caller
from src.commands.payments import Payments
from src.gui.print import print_error_panel
from src.gui.tables import display_user_details
from src.utils import (
    clean_nigerian_states,
    create_disk_cached_function,
    export_member_data_by_state,
    convert_to_vcf,
    save_dataframe,
)
from src.types import OutputFormat

app = typer.Typer(name="user")


class User:

    @api_caller
    @staticmethod
    def get_user_id_from_member_id(member_id: int, **kwargs) -> Optional[None]:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/user_id",
                headers=get_headers(token),
                json=dict(member_id=member_id),
            )

            response.raise_for_status()

            if "user_id" in response.json():
                print(
                    'User ID for ->{}<- Member ID is "{}"'.format(
                        member_id, response.json().get("user_id")
                    )
                )
                return response.json().get("user_id")
        except HTTPError:
            print_error_panel("Member ID Could not be found")
            return None

    @api_caller
    @staticmethod
    def get_user_information(user_id: int, **kwargs) -> Optional[dict[str, str]]:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/user",
                headers=get_headers(token),
                json=dict(user_id=user_id),
            )

            response.raise_for_status()

            if "data" in response.json():
                if "user_id" in response.json()["data"]:
                    if response.json()["data"]["user_id"].strip() != "":
                        return response.json()["data"]
                    else:
                        print_error_panel("User ID is not found in dataset")
                        return None
                else:
                    print_error_panel("Dataset returned is empty")
                    return None
            else:
                print_error_panel("Dataset is an invalid response")
                return None
        except HTTPError:
            print_error_panel("Member ID Could not be found")
            return None

    @api_caller
    @staticmethod
    def get_all_users(**kwargs) -> dict:  # type: ignore
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/all-users",
                headers=get_headers(token),
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print_error_panel(str(e))
            typer.Exit(1)

    @api_caller
    @staticmethod
    def all_info_about_users(*args, **kwargs) -> Optional[dict]:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/data/get-all",
                headers=get_headers(token),
            )

            response.raise_for_status()

            return response.json()
        except HTTPError as e:
            print(e)
            print_error_panel("Http Error Experienced Here")
            return None
            # typer.Exit()

    @api_caller
    @staticmethod
    def all_users_with_partial_payment(*args, **kwargs) -> Optional[dict]:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/data/users/partial-payment-latest",
                headers=get_headers(token),
            )

            response.raise_for_status()

            return response.json()
        except HTTPError as e:
            print(e)
            print_error_panel("Http Error Experienced Here")
            return None
            # typer.Exit()

    @api_caller
    @staticmethod
    def all_users_without_payment(*args, **kwargs) -> Optional[dict]:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/data/users/no-payment-latest",
                headers=get_headers(token),
            )

            response.raise_for_status()

            return response.json()
        except HTTPError as e:
            print(e)
            print_error_panel("Http Error Experienced Here")
            return None

    @api_caller
    @staticmethod
    def all_users_with_complete_payment(*args, **kwargs) -> Optional[dict]:
        session: Session = kwargs["session"]
        token: str = kwargs["token"]
        root_url: str = kwargs["root_url"]

        try:
            response = session.get(
                f"{root_url.rstrip('/')}/data/users/complete-payment-latest",
                headers=get_headers(token),
            )
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            print(e)
            print_error_panel("Http Error Experienced Here")
            return None

    @staticmethod
    def rename_columns(dp: pd.DataFrame) -> pd.DataFrame:
        return dp.rename(
            columns={
                "1": "first_name",
                "3": "nickname",
                "877": "company",
                "873": "job_title",
                "6": "marital_status",
                "557": "gender",
                "561": "dob",
                "5": "phone_no",
                "917": "country",
                "22": "address_1",
                "888": "nsa_member_id",
                "21": "company_address",
                "276": "state",
                "25": "city",
                "24": "postcode",
                "23": "address_2",
                "1425": "profession_status",
                "859": "education_type_1",
                "840": "education_type_2",
                "839": "course_major",
                "836": "education_location",
                "835": "education_institution",
                "2": "last_name",
                "538": "title",
                "864": "middle_name",
                "894": "member_id",
            }
        )


@app.command(name="get-memberid")
def get_user_id_from_member_id(
    member_id=typer.Argument(..., help="member_id of a user to get the actual ID")
):
    User.get_user_id_from_member_id(member_id)


@app.command(name="about")
def get_user_information(user_id=typer.Argument(..., help="The actual ID of a user")):
    response = User.get_user_information(user_id)
    if response:
        display_user_details(response)


@app.command(name="uifmid", help="User Information from Member ID")
def get_user_information_from_member_id(
    member_id=typer.Argument(..., help="member_id of a user to get the actual ID")
):
    response1 = User.get_user_id_from_member_id(member_id)
    if response1:
        response2 = User.get_user_information(response1)
        if response2:
            print(response2)
            display_user_details(response2)


@app.command(name="state", help="categorize the users into states")
def get_states_for_users():
    get_cached_user_info = create_disk_cached_function(
        User.all_info_about_users, cache_directory=".user_data_cache"
    )
    response = get_cached_user_info()

    if response:
        # print(response['data'][0])
        data = User.rename_columns(pd.DataFrame(response["data"]))

        data["state"] = data["state"].apply(clean_nigerian_states)
        export_member_data_by_state(data, "state")


@app.command(name="search", help="Search for anything in the user details")
def search(
    ctx: typer.Context,
    value: str = typer.Argument(..., help="value you want to search"),
):
    get_cached_user_info = create_disk_cached_function(
        User.all_info_about_users, cache_directory=".cache/users"
    )
    user = get_cached_user_info()

    data = pd.DataFrame(user["data"])

    if data.empty:
        print("User database is empty.")
        raise typer.Exit()

    matching_mask = data.astype(str).apply(
        lambda col: col.str.contains(value, case=False, na=False)
    )

    matching_rows = data[matching_mask.any(axis=1)]

    if len(matching_rows) > 0:
        print(f"\nFound {len(matching_rows)} Occurrence(s):\n")

        safe_value = "".join(
            c for c in value if c.isalnum() or c in (" ", "_", "-")
        ).rstrip()
        file_name = f"search_{safe_value}.csv"
        print(matching_rows.head())
        matching_rows = User.rename_columns(matching_rows)
        matching_rows = matching_rows[
            [
                "first_name",
                "last_name",
                "middle_name",
                "member_id",
                "marital_status",
                "phone_no",
                "company",
                "title",
            ]
        ]
        convert_to_vcf(matching_rows, value, suffix=f"CISON {value}")
        matching_rows.to_csv(file_name, index=False)
        print(f"\nResults exported to {file_name}")
    else:
        print("Found Nothing")


@app.command(
    name="vmwcp", help="Valid members holding certificate and complete payment"
)
def complete_payment_with_certificates():
    from src.commands.certificates.membership import Membership

    get_cached_certificates = create_disk_cached_function(
        Membership.get_all_certificates, cache_directory="certificates"
    )

    get_cached_user_info = create_disk_cached_function(
        User.all_info_about_users, cache_directory="all_users"
    )
    response = get_cached_user_info()

    data = pd.DataFrame(response["data"])
    data = User.rename_columns(data)

    complete = []
    certs = get_cached_certificates()
    for i in tqdm.tqdm(certs["data"]):
        user_info = User.get_user_information(i["user_id"])
        if all(user_info["paid_fees"].values()):
            user_data = data[data.member_id == user_info["member_id"]]
            user_data = user_data.to_dict(orient="records")[0]
            complete.append(user_data)

    df = pd.DataFrame(complete)
    df = df[["first_name", "last_name", "middle_name", "member_id", "phone_no"]]
    df.to_csv("complete.csv")


@app.command("partial-payments")
def get_partial_payments(
    ctx: typer.Context,
    filename: Optional[str] = typer.Option(
        None,
        "--filename",
        "-f",
        help="Output filename (defaults to command name: partial-payments)",
    ),
    fmt: OutputFormat = typer.Option(
        OutputFormat.csv,
        "--format",
        "-fmt",
        help="Format to save output to",
    ),
):
    """Fetch all users with partial payments and save to disk."""
    function = create_disk_cached_function(
        Payments.get_users_with_partial_payments, "partial_payment"
    )
    data = function()
    if data is None:
        raise typer.Exit(code=1)

    save_dataframe(
        data=data,
        filename=filename,
        default_name="partial-payments",
        output_format=fmt,
    )


@app.command("no-payments")
def get_no_payments(
    ctx: typer.Context,
    filename: Optional[str] = typer.Option(
        None,
        "--filename",
        "-f",
        help="Output filename (defaults to command name: no-payments)",
    ),
    fmt: OutputFormat = typer.Option(
        OutputFormat.csv,
        "--format",
        "-fmt",
        help="Format to save output to",
    ),
):
    """Fetch all users without any payments and save to disk."""
    function = create_disk_cached_function(
        Payments.get_users_without_payments, "without_payment"
    )
    data = function()
    if data is None:
        raise typer.Exit(code=1)

    save_dataframe(
        data=data,
        filename=filename,
        default_name="no-payments",
        output_format=fmt,
    )


@app.command("complete-payments")
def get_complete_payments(
    ctx: typer.Context,
    filename: Optional[str] = typer.Option(
        None,
        "--filename",
        "-f",
        help="Output filename (defaults to command name: complete-payments)",
    ),
    fmt: OutputFormat = typer.Option(
        OutputFormat.csv,
        "--format",
        "-fmt",
        help="Format to save output to",
    ),
):
    """Fetch all users with complete payments and save to disk."""
    function = create_disk_cached_function(
        Payments.get_users_with_complete_payments, "complete_payment"
    )

    data = function()
    
    if data is None:
        raise typer.Exit(code=1)

    save_dataframe(
        data=data,
        filename=filename,
        default_name="complete-payments",
        output_format=fmt,
    )
