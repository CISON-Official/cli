from copy import deepcopy
from typing import Literal

import requests
import typer
from rich import print_json

from src.__email import get_email_header
from src.config import setting
from src.email.base import EmailBase
from src.gui.print import confirm_action, print_error_panel, print_success_panel
from src.gui.tables import display_all_mailing_list

app: typer.Typer = typer.Typer(name="mailinglist")


def _build_contactinfo(
    contact_email: str,
    firstname: str | None = None,
    lastname: str | None = None,
) -> str:
    """Build the {key:value,...} style contactinfo string Zoho expects."""
    fields = {"Contact Email": contact_email}
    if firstname:
        fields["First Name"] = firstname
    if lastname:
        fields["Last Name"] = lastname
    return "{" + ",".join(f"{k}:{v}" for k, v in fields.items()) + "}"


class MailingList(EmailBase):
    def get_mailing_list(
        self,
        id: str | None = None,
        sort: Literal["asc", "desc"] = "asc",
        fromindex: int | None = None,
        range: int | None = None,
    ) -> str | dict | None:

        params = {"resfmt": "JSON", "sort": sort}
        if fromindex:
            params["fromindex"] = fromindex  # type: ignore
        if range:
            params["range"] = range  # type: ignore

        response = requests.post(
            f"{setting.EMAIL_API_BASE}/getmailinglists",
            params=params,
            headers=get_email_header(self.access_token),
        )

        data = response.json()

        if data.get("status") and data.get("status") == "success":
            details = data.get("list_of_details")
            if id:
                if single := filter(lambda x: x["listkey"] == id, details):
                    for i in single:
                        print_json(data=i)
                        return i
                print_error_panel("Unable to get mailinglist")
                return

            else:
                display_all_mailing_list(data)
                return data
        else:
            print_error_panel("Unable to get mailinglist")

    def get_list_advanced_details(
        self,
        listkey: str,
        filtertype: (
            Literal["sentcampaigns", "scheduledcampaigns", "recentcampaigns"] | None
        ) = None,
        fromindex: int | None = None,
        range: int | None = None,
    ) -> dict | None:
        params = {"resfmt": "JSON", "listkey": listkey}
        if filtertype:
            params["filtertype"] = filtertype
        if fromindex:
            params["fromindex"] = fromindex  # type: ignore
        if range:
            params["range"] = range  # type: ignore

        try:
            response = requests.get(
                f"{setting.EMAIL_API_BASE}/getlistadvanceddetails",
                params=params,
                headers=get_email_header(self.access_token),
            )
            response.raise_for_status()

            data = response.json()
            print_json(data=data)
            return data
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting list advanced details")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def get_list_contacts(
        self,
        listkey: str,
        sort: Literal["asc", "desc"] = "asc",
        status: (
            Literal["active", "recent", "mostrecent", "unsub", "bounce"] | None
        ) = None,
        fromindex: int | None = None,
        range: int | None = None,
    ) -> dict | None:
        params = {"resfmt": "JSON", "listkey": listkey, "sort": sort}
        if status:
            params["status"] = status
        if fromindex:
            params["fromindex"] = fromindex  # type: ignore
        if range:
            params["range"] = range  # type: ignore

        try:
            response = requests.get(
                f"{setting.EMAIL_API_BASE}/getlistsubscribers",
                params=params,
                headers=get_email_header(self.access_token),
            )
            response.raise_for_status()

            data = response.json()
            print_json(data=data)
            return data
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting list contacts")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def get_all_contact_fields(
        self, type: Literal["xml", "json"] = "json"
    ) -> dict | None:
        params = {"type": type}

        try:
            response = requests.get(
                f"{setting.EMAIL_API_BASE}/contact/allfields",
                params=params,
                headers=get_email_header(self.access_token),
            )
            response.raise_for_status()

            data = response.json()
            print_json(data=data)
            return data
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting contact fields")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def get_segment_details(self, listkey: str, cvid: str) -> dict | None:
        params = {"resfmt": "JSON", "listkey": listkey, "cvid": cvid}

        try:
            response = requests.get(
                f"{setting.EMAIL_API_BASE}/getsegmentdetails",
                params=params,
                headers=get_email_header(self.access_token),
            )
            response.raise_for_status()

            data = response.json()
            print_json(data=data)
            return data
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting segment details")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def get_segment_contacts(self, cvid: str) -> dict | None:
        params = {"resfmt": "JSON", "cvid": cvid}

        try:
            response = requests.get(
                f"{setting.EMAIL_API_BASE}/getsegmentcontacts",
                params=params,
                headers=get_email_header(self.access_token),
            )
            response.raise_for_status()

            data = response.json()
            print_json(data=data)
            return data
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting segment contacts")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def update_list(
        self,
        listkey: str,
        newlistname: str,
        signupform: Literal["public", "private"],
    ) -> bool:
        params = {
            "resfmt": "JSON",
            "listkey": listkey,
            "newlistname": newlistname,
            "signupform": signupform,
        }

        try:
            response = requests.post(
                f"{setting.EMAIL_API_BASE}/updatelistdetails",
                params=params,
                headers=get_email_header(self.access_token),
            )
            response.raise_for_status()

            data = response.json()
            if data.get("status") == "success":
                print_success_panel("List updated successfully.")
                return True
            print_error_panel(f"Unable to update list {listkey}")
            return False
        except requests.exceptions.HTTPError:
            print_error_panel("Error while updating list")
            return False
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return False

    def delete_mailing_list(
        self, listkey: str, deletecontact: Literal["off", "on"] = "on"
    ) -> bool:
        params = {"resfmt": "JSON", "deletecontacts": deletecontact, "listkey": listkey}
        try:
            response = requests.get(
                f"{setting.EMAIL_API_BASE}/deletemailinglist",
                params=params,
                headers=get_email_header(self.access_token),
            )
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "success":
                print_success_panel("Mailing list have successfully be deleted")
                return True
            print(data)
            print_error_panel(f"Unable to delete mailinglist {listkey}")
            return False

        except requests.exceptions.HTTPError:
            print_error_panel("Error while deleting mailing list")
            return False
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return False

    def total_contacts(
        self,
        listkey: str,
        status: Literal["active", "unsub", "bounce", "spam"] | None = None,
    ) -> int | None:
        params = {"resfmt": "JSON", "listkey": listkey}
        if status:
            params["status"] = status

        try:
            response = requests.get(
                f"{setting.EMAIL_API_BASE}/listsubscriberscount",
                params=params,
                headers=get_email_header(self.access_token),
            )
            response.raise_for_status()

            data = response.json()
            if data.get("status") == "success":
                print_success_panel(f"Total contacts: {data.get('no_of_contacts')}")
                return data.get("no_of_contacts")
            print_error_panel("Unable to get total contacts")
            return None
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting total contacts")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def subscribe(
        self,
        listkey: str,
        contact_email: str,
        firstname: str | None = None,
        lastname: str | None = None,
        source: str | None = None,
        topic_id: str | None = None,
        payload: dict | None = None,
    ) -> bool:
        self.params["listkey"] = listkey
        self.params["resfmt"] = "JSON"
        if payload:
            self.params["contactinfo"] = payload
        else:
            self.params["contactinfo"] = _build_contactinfo(
                contact_email, firstname, lastname
            )
        if source:
            self.params["source"] = source
        if topic_id:
            self.params["topic_id"] = topic_id

        try:
            response = requests.post(
                f"{setting.EMAIL_API_BASE}/json/listsubscribe",
                params=self.params,
                headers=self.get_header(),
            )
            response.raise_for_status()

            data = response.json()
            if data.get("status") == "success":
                print_success_panel(data.get("message", "Contact subscribed."))
                return True
            print_error_panel(f"Unable to subscribe {contact_email}")
            return False
        except requests.exceptions.HTTPError as e:
            print_error_panel(f"Error while subscribing contact {e}")
            return False
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return False

    def unsubscribe(
        self,
        listkey: str,
        contact_email: str,
        firstname: str | None = None,
        lastname: str | None = None,
        topic_id: str | None = None,
    ) -> bool:
        self.params["listkey"] = listkey
        self.params["resfmt"] = "JSON"
        self.params["contactinfo"] = _build_contactinfo(
            contact_email, firstname, lastname
        )
        if topic_id:
            self.params["topic_id"] = topic_id

        try:
            response = requests.post(
                f"{setting.EMAIL_API_BASE}/json/listunsubscribe",
                params=self.params,
                headers=self.get_header(),
            )
            response.raise_for_status()

            data = response.json()
            if data.get("status") == "success":
                print_success_panel(data.get("message", "Contact unsubscribed."))
                return True
            print_error_panel(f"Unable to unsubscribe {contact_email}")
            return False
        except requests.exceptions.HTTPError as e:
            print_error_panel(f"Error while unsubscribing contact {e}")
            return False
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return False

    def move_to_do_not_mail(self, contact_email: str) -> bool:
        self.params["resfmt"] = "JSON"
        self.params["contactinfo"] = _build_contactinfo(contact_email)

        try:
            response = requests.post(
                f"{setting.EMAIL_API_BASE}/json/contactdonotmail",
                params=self.params,
                headers=self.get_header(),
            )
            response.raise_for_status()

            data = response.json()
            if data.get("code") == "0" or data.get("status") == "success":
                print_success_panel(
                    data.get("message", "Contact moved to Do-Not-Mail.")
                )
                return True
            print_error_panel(f"Unable to move {contact_email} to Do-Not-Mail")
            return False
        except requests.exceptions.HTTPError as e:
            print_error_panel(f"Error while moving contact to Do-Not-Mail {e}")
            return False
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return False

    def add_contacts_existing_list(self, listkey: str, emailids: list[str]) -> bool:
        self.params["listkey"] = listkey
        self.params["resfmt"] = "JSON"
        self.params["emailids"] = ",".join(emailids)

        try:
            response = requests.post(
                f"{setting.EMAIL_API_BASE}/addlistsubscribersinbulk",
                params=self.params,
                headers=self.get_header(),
            )
            response.raise_for_status()

            data = response.json()
            print(data)
            if data.get("status") == "success":
                print_success_panel(
                    f"Successfully added contacts to list: {data.get('listname')}"
                )
                return True
            print_error_panel(f"Unable to add contacts to list {listkey}")
            print(data)
            return False
        except requests.exceptions.HTTPError as e:
            print_error_panel(f"Error while adding contacts to list {e}")
            return False
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return False

    def create_mailing_list(
        self,
        emailids: list[str],
        listname: str,
        signupform: Literal["public", "private"],
        listdescription: str | None = None,
    ) -> str | None:

        params = deepcopy(self.params)

        params["emailids"] = ",".join(emailids)
        params["listname"] = listname
        params["signupform"] = signupform
        params["mode"] = "newlist"
        params["resfmt"] = "JSON"
        if listdescription:
            params["listdescription"] = listdescription

        try:
            response = requests.post(
                f"{setting.EMAIL_API_BASE}/addlistandcontacts",
                params=params,
                headers=self.get_header(),
            )
            response.raise_for_status()

            data = response.json()
            if data.get("status") == "success":
                print_success_panel(
                    f"Successfully created list: {data.get('listname')} "
                    f"({data.get('listkey')})"
                )
                return data.get("listkey")
            print(data)
            print_error_panel("Unable to create mailing list")
            return None
        except requests.exceptions.HTTPError as e:
            print_error_panel(f"Error while creating mailing list {e}")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def create_custom_field(
        self,
        fieldname: str,
        fieldtype: Literal[
            "Text",
            "Integer",
            "Phone",
            "Date",
            "Picklist",
            "Email",
            "Checkbox",
            "LongInteger",
            "URL",
            "textarea",
            "RadioOption",
            "Multiselect",
            "DateTime",
            "Decimal",
            "Percent",
        ],
        fieldlength: int | None = None,
        type: Literal["xml", "json"] = "json",
    ) -> bool:
        self.params["type"] = type
        self.params["fieldname"] = fieldname
        self.params["fieldtype"] = fieldtype
        if fieldlength:
            self.params["fieldlength"] = fieldlength

        try:
            response = requests.post(
                f"{setting.EMAIL_API_BASE}/custom/add",
                params=self.params,
                headers=self.get_header(),
            )
            response.raise_for_status()

            data = response.json()
            payload = data.get("response", data)
            if payload.get("message") == "Success" or payload.get("code") == "200":
                print_success_panel(f"Successfully created custom field: {fieldname}")
                return True
            print_error_panel(f"Unable to create custom field {fieldname}")
            return False
        except requests.exceptions.HTTPError as e:
            print_error_panel(f"Error while creating custom field {e}")
            return False
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return False


@app.command(
    name="get",
    help="get all mailing list or retireve a single mailing list using the ID",
)
def get_mailing_list(
    ctx: typer.Context,
    listkey=typer.Option(None, "--listkey", "-l", help="Mailing List listkey"),
    sort: Literal["asc", "desc"] = typer.Option("asc", "--sort"),
    fromindex: int = typer.Option(1, "--fromindex"),
    range: int = typer.Option(100, "--range"),
):

    kwargs = {}
    # loader = ctx.obj
    if listkey:
        kwargs["id"] = listkey
    #     loader.update(f"Filtering getting mailinglist with id: {listkey}")
    # else:
    #     loader.update("Retrieving members eligible for membership certificate...")

    if ctx.obj:
        ctx.obj.stop()

    if sort:
        kwargs["sort"] = sort
    if fromindex:
        kwargs["fromindex"] = fromindex
    if range:
        kwargs["range"] = range

    mailing_list = MailingList()
    mailing_list.get_mailing_list(**kwargs)


@app.command(
    name="advanced-details",
    help="get advanced details (stats, contact details, campaigns sent) for a list",
)
def get_list_advanced_details(
    listkey: str = typer.Argument(..., help="Mailing List listkey"),
    filtertype: str | None = typer.Option(
        None,
        "--filtertype",
        help="sentcampaigns/scheduledcampaigns/recentcampaigns",
    ),
    fromindex: int = typer.Option(1, "--fromindex"),
    range: int = typer.Option(100, "--range"),
):
    mailing_list = MailingList()
    mailing_list.get_list_advanced_details(
        listkey=listkey,
        filtertype=filtertype,
        fromindex=fromindex,
        range=range,  # type: ignore
    )


@app.command(name="contacts", help="get the contacts belonging to a mailing list")
def get_list_contacts(
    listkey: str = typer.Argument(..., help="Mailing List listkey"),
    sort: Literal["asc", "desc"] = typer.Option("asc", "--sort"),
    status: str | None = typer.Option(
        None, "--status", help="active/recent/mostrecent/unsub/bounce"
    ),
    fromindex: int = typer.Option(1, "--fromindex"),
    range: int = typer.Option(100, "--range"),
):
    mailing_list = MailingList()
    mailing_list.get_list_contacts(
        listkey=listkey,
        sort=sort,
        status=status,
        fromindex=fromindex,
        range=range,  # type: ignore
    )


@app.command(name="fields", help="get all available contact fields")
def get_all_contact_fields(
    type: Literal["xml", "json"] = typer.Option("json", "--type"),
):
    mailing_list = MailingList()
    mailing_list.get_all_contact_fields(type=type)


@app.command(name="segment-details", help="get details for a segment")
def get_segment_details(
    listkey: str = typer.Argument(..., help="Mailing List listkey"),
    cvid: str = typer.Argument(
        ..., help="Segment/criteria view ID from getmailinglists"
    ),
):
    mailing_list = MailingList()
    mailing_list.get_segment_details(listkey=listkey, cvid=cvid)


@app.command(name="segment-contacts", help="get the contacts belonging to a segment")
def get_segment_contacts(
    cvid: str = typer.Argument(
        ..., help="Segment/criteria view ID from getmailinglists"
    ),
):
    mailing_list = MailingList()
    mailing_list.get_segment_contacts(cvid=cvid)


@app.command(name="update", help="rename a list or update its signup form visibility")
def update_list(
    listkey: str = typer.Argument(..., help="Mailing List listkey"),
    newlistname: str = typer.Option(..., "--newlistname", "-n"),
    signupform: Literal["public", "private"] = typer.Option(..., "--signupform"),
):
    mailing_list = MailingList()
    mailing_list.update_list(
        listkey=listkey, newlistname=newlistname, signupform=signupform
    )


@app.command(name="delete", help="delete a mailing list using the listkey")
def delete_mailing_list(
    ctx: typer.Context, listkey=typer.Argument(..., help="Mailing List listkey")
):
    # loader = ctx.obj
    # loader.update(f"Deleting mailinglist with id: {listkey}")
    kwargs = {"listkey": listkey}
    kwargs["deletecontact"] = (
        "on" if confirm_action("Do you want to also delete the contacts? ") else "off"
    )
    mailing = MailingList()
    mailing.delete_mailing_list(**kwargs)


@app.command(name="total-contacts", help="get the total number of contacts in a list")
def total_contacts(
    listkey: str = typer.Argument(..., help="Mailing List listkey"),
    status: str | None = typer.Option(
        None, "--status", help="active/unsub/bounce/spam"
    ),
):
    mailing_list = MailingList()
    mailing_list.total_contacts(listkey=listkey, status=status)  # type: ignore


@app.command(name="subscribe", help="add/subscribe a contact to a mailing list")
def subscribe(
    listkey: str = typer.Argument(..., help="Mailing List listkey"),
    contact_email: str = typer.Option(..., "--email", "-e"),
    firstname: str | None = typer.Option(None, "--firstname"),
    lastname: str | None = typer.Option(None, "--lastname"),
    source: str | None = typer.Option(None, "--source"),
    topic_id: str | None = typer.Option(None, "--topic-id"),
):
    mailing_list = MailingList()
    mailing_list.subscribe(
        listkey=listkey,
        contact_email=contact_email,
        firstname=firstname,
        lastname=lastname,
        source=source,
        topic_id=topic_id,
    )


@app.command(name="unsubscribe", help="unsubscribe a contact from a mailing list")
def unsubscribe(
    listkey: str = typer.Argument(..., help="Mailing List listkey"),
    contact_email: str = typer.Option(..., "--email", "-e"),
    firstname: str | None = typer.Option(None, "--firstname"),
    lastname: str | None = typer.Option(None, "--lastname"),
    topic_id: str | None = typer.Option(None, "--topic-id"),
):
    mailing_list = MailingList()
    mailing_list.unsubscribe(
        listkey=listkey,
        contact_email=contact_email,
        firstname=firstname,
        lastname=lastname,
        topic_id=topic_id,
    )


@app.command(name="do-not-mail", help="move a contact to the Do-Not-Mail registry")
def move_to_do_not_mail(
    contact_email: str = typer.Argument(..., help="Contact email address"),
):
    mailing_list = MailingList()
    mailing_list.move_to_do_not_mail(contact_email=contact_email)


@app.command(
    name="add-contacts",
    help="add contacts (max 10 emails) to an existing mailing list",
)
def add_contacts_existing_list(
    listkey: str = typer.Argument(..., help="Mailing List listkey"),
    emailids: str = typer.Option(
        ..., "--emails", "-e", help="Comma separated list of up to 10 email addresses"
    ),
):
    keys_list = [k.strip() for k in emailids.split(",") if k.strip()]
    mailing_list = MailingList()
    mailing_list.add_contacts_existing_list(listkey=listkey, emailids=keys_list)


@app.command(name="create", help="create a new mailing list and add contacts to it")
def create_mailing_list(
    listname: str = typer.Argument(
        ...,
    ),
    signupform: Literal["public", "private"] = typer.Option(..., "--signupform"),
    emailids: str = typer.Option(
        ..., "--emails", "-e", help="Comma separated list of up to 10 email addresses"
    ),
    listdescription: str | None = typer.Option(None, "--description"),
):
    keys_list = [k.strip() for k in emailids.split(",") if k.strip()]
    mailing_list = MailingList()
    mailing_list.create_mailing_list(
        emailids=keys_list,
        listname=listname,
        signupform=signupform,
        listdescription=listdescription,
    )


@app.command(name="create-field", help="create a custom contact field")
def create_custom_field(
    fieldname: str = typer.Argument(..., help="Name of the custom field"),
    fieldtype: str = typer.Option(
        ...,
        "--fieldtype",
        help=(
            "Text/Integer/Phone/Date/Picklist/Email/Checkbox/LongInteger/URL/"
            "textarea/RadioOption/Multiselect/DateTime/Decimal/Percent"
        ),
    ),
    fieldlength: int | None = typer.Option(
        None, "--fieldlength", help="Defaults to 20 if not provided"
    ),
):
    mailing_list = MailingList()
    mailing_list.create_custom_field(
        fieldname=fieldname,
        fieldtype=fieldtype,
        fieldlength=fieldlength,  # type: ignore
    )
