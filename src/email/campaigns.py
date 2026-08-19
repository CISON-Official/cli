#!/usr/bin/env python3

"""Campaign operations for the Zoho Campaigns API."""

import json
from typing import Optional, Literal, Union

import typer
import requests

import questionary
from src.config import setting
from src.email.base import EmailBase
from src.exception import handle_error
from src.gui.print import print_error_panel, print_success_panel
from src.gui.tables import display_single_campaign_details, display_all_campaigns

app = typer.Typer(
    name="campaign",
    help="Create, schedule, send, and manage Zoho Campaigns email campaigns.",
)

CampaignStatus = Literal[
    "all",
    "all campaigns",
    "drafts",
    "scheduled",
    "inprogress",
    "sent",
    "stopped",
    "canceled",
    "tobereviewed",
    "reviewed",
    "paused",
    "intesting",
]

RecipientAction = Literal[
    "sentcontacts",
    "openedcontacts",
    "optoutcontacts",
    "spamcontacts",
    "unopenedcontacts",
    "clickedcontacts",
    "senthardbounce",
    "sentsoftbounce",
    "unsentcontacts",
]


class EmailCampaign(EmailBase):

    def single_campaigns(
        self, campaignkey: str, campaigntype: Literal["normal", "abtesting"]
    ) -> list:
        try:
            self.params["campaigntype"] = campaigntype
            self.params["campaignkey"] = campaignkey

            response = requests.get(
                f"{setting.EMAIL_API_BASE}/getcampaigndetails",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            handle_error(data)
            print(data)
            display_single_campaign_details(data)
            return []
        except requests.exceptions.HTTPError:
            print_error_panel("Error while deleting mailing list")
            return []
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return []

    def list_campaigns(
        self,
        sort: Literal["asc", "desc"] = "asc",
        status: Union[CampaignStatus, list[CampaignStatus]] = "all",
        fromindex: Optional[int] = None,
        range: Optional[int] = None,
    ) -> list:
        try:
            self.params["sort"] = sort
            self.params["status"] = status  # type: ignore

            if fromindex:
                self.params["fromindex"] = fromindex  # type: ignore

            if range:
                self.params["range"] = range  # type: ignore

            response = requests.get(
                f"{setting.EMAIL_API_BASE}/recentcampaigns",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            handle_error(data)
            display_all_campaigns(data)
            return []
        except requests.exceptions.HTTPError:
            print_error_panel(f"Error while getting {status} campaigns")
            return []
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return []

    def create_campaign(
    self,
        campaign_name: str,
        subject: str,
        list_details: list[str],
        content_url: str,
    ) -> Optional[str]:
        try:
            
            list_details_dict = {list_key: [] for list_key in list_details}
            
            list_details_json_string = json.dumps(list_details_dict, separators=(',', ':')) 

            self.params["campaignname"] = campaign_name
            self.params["subject"] = subject
            self.params["content_url"] = content_url
            self.params["from_email"] = str(setting.EMAIL_ADMIN)
            self.params["from_name"] = str(setting.PROGRAM_NAME)
            self.params["topicId"] = "1448394000000047017"
            
            self.params["list_details"] = list_details_json_string

            response = requests.post(
                f"{setting.EMAIL_API_BASE}/createCampaign",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()
            data = response.json()
            
            
            if data.get("code") == "200":
                print_success_panel(f"Successfully created campaign with ID: {data.get('campaignKey')}")
                return data.get("campaignKey")
            else:
                print_error_panel(f"API Error during creation: {data}")
                return None

        except requests.exceptions.HTTPError as e:
            print_error_panel(f"HTTP Error while creating campaigns: {e}")
            # Print response text for debugging
            if hasattr(e, 'response') and e.response is not None:
                print_error_panel(f"Response: {e.response.text}")
            return None
        except Exception as e:
            print_error_panel(f"Unexpected error: {e}")
            return None   

    def send_campaign(self, campaignkey: str, list_details=[]) -> bool:
        try:
            list_details_dict = {list_key: [] for list_key in list_details}
            list_details_json_string = json.dumps(list_details_dict)
            
            self.params["resfmt"] = "JSON"
            self.params["campaignkey"] = campaignkey
            self.params["list_details"] = list_details_json_string

            response = requests.post(
                f"{setting.EMAIL_API_BASE}/sendcampaign",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            payload = data.get("response", data)
            handle_error(payload)
            print_success_panel(
                f"Campaign status: {payload.get('campaign_status', 'sent')}"
            )
            return True
        except requests.exceptions.HTTPError as e:
            print_error_panel(f"Error while sending campaign {e}")
            return False
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return False

    def schedule_campaign(
        self,
        campaignkey: str,
        scheduledate: str,
        schedulehour: str,
        scheduleminute: str,
        am_pm: Literal["AM", "PM"],
        istimewarp: Optional[bool] = None,
        sendingtz: Optional[str] = None,
    ) -> bool:
        try:
            self.params["resfmt"] = "JSON"
            self.params["campaignkey"] = campaignkey
            self.params["scheduledate"] = scheduledate
            self.params["schedulehour"] = schedulehour
            self.params["scheduleminute"] = scheduleminute
            self.params["am_pm"] = am_pm
            if istimewarp is not None:
                self.params["istimewarp"] = istimewarp
            if sendingtz:
                self.params["sendingTZ"] = sendingtz

            response = requests.post(
                f"{setting.EMAIL_API_BASE}/sendcampaign",
                params={**self.params, "isschedule": "true"},
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            handle_error(data)
            print_success_panel(
                f"Campaign status: {data.get('campaign_status', 'scheduled')}"
            )
            return True
        except requests.exceptions.HTTPError as e:
            print_error_panel(f"Error while scheduling campaign {e}")
            return False
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return False

    def clone_campaign(
        self,
        oldcampaignkey: str,
        campaignname: str,
        subject: str,
        from_name: Optional[str] = None,
        from_add: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> None:
        try:
            campaigninfo = {
                "campaignname": campaignname,
                "subject": subject,
                "oldcampaignkey": oldcampaignkey,
                "encode_type": "UTF-8",
            }
            if from_name:
                campaigninfo["from_name"] = from_name
            if from_add:
                campaigninfo["from_add"] = from_add
            if reply_to:
                campaigninfo["reply_to"] = reply_to

            self.params["resfmt"] = "JSON"
            self.params["campaigninfo"] = json.dumps(campaigninfo)

            response = requests.post(
                f"{setting.EMAIL_API_BASE}/json/clonecampaign",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            handle_error(data)
            print_success_panel(f"Successfully cloned campaign: {campaignname}")
            return
        except requests.exceptions.HTTPError as e:
            print_error_panel(f"Error while cloning campaign {e}")
            return
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return

    def campaign_reports(self, campaignkey: str) -> Optional[dict]:
        try:
            self.params["resfmt"] = "JSON"
            self.params["campaignkey"] = campaignkey

            response = requests.get(
                f"{setting.EMAIL_API_BASE}/campaignreports",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            handle_error(data)
            display_single_campaign_details(data)
            return data
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting campaign reports")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def recently_sent_campaigns(self) -> Optional[dict]:
        try:
            self.params["resfmt"] = "JSON"

            response = requests.get(
                f"{setting.EMAIL_API_BASE}/recentsentcampaigns",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            handle_error(data)
            display_all_campaigns(data)
            return data
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting recently sent campaigns")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def last_campaign_report(self) -> Optional[dict]:
        try:
            self.params["resfmt"] = "JSON"

            response = requests.post(
                f"{setting.EMAIL_API_BASE}/getlastcampaignreport",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            handle_error(data)
            display_single_campaign_details(data)
            return data
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting last campaign report")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def campaign_recipients_data(
        self, campaignkey: str, action: RecipientAction
    ) -> Optional[dict]:
        try:
            self.params["resfmt"] = "JSON"
            self.params["campaignkey"] = campaignkey
            self.params["action"] = action

            response = requests.post(
                f"{setting.EMAIL_API_BASE}/getcampaignrecipientsdata",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            handle_error(data)
            print_success_panel(
                f"Found {len(data.get('list_of_details', []))} contacts for '{action}'"
            )
            print(data)
            return data
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting campaign recipients data")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def view_coupon_details(self, couponcode: str) -> Optional[dict]:
        try:
            self.params["type"] = "json"
            self.params["couponCode"] = couponcode

            response = requests.post(
                f"{setting.EMAIL_API_BASE}/coupon/coupondetails",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            payload = data.get("response", data)
            handle_error(payload)
            print(payload.get("CouponDetails", payload))
            return data
        except requests.exceptions.HTTPError:
            print_error_panel("Error while getting coupon details")
            return None
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return None

    def change_coupon_status(self, couponcode: str, changestatus: str = "used") -> bool:
        try:
            self.params["type"] = "json"
            self.params["couponCode"] = couponcode
            self.params["changeStatus"] = changestatus

            response = requests.get(
                f"{setting.EMAIL_API_BASE}/coupon/changestatus",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            payload = data.get("response", data)
            handle_error(payload)
            print_success_panel(payload.get("message", "Coupon status changed"))
            return True
        except requests.exceptions.HTTPError as e:
            print_error_panel(f"Error while changing coupon status {e}")
            return False
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return False

    def delete_campaign(self, campaignkey: str) -> bool:
        try:
            self.params["resfmt"] = "JSON"
            self.params["campaignkey"] = campaignkey

            response = requests.get(
                f"{setting.EMAIL_API_BASE}/deletecampaign",
                params=self.params,
                headers=self.get_header(),
            )

            response.raise_for_status()

            data = response.json()
            handle_error(data)
            print_success_panel(f"Successfully deleted campaign: {campaignkey}")
            return True
        except requests.exceptions.HTTPError:
            print_error_panel("Error while deleting campaign")
            return False
        except requests.exceptions.JSONDecodeError:
            print_error_panel("Error while decoding to json")
            return False


@app.command("single")
def single_campaigns(
    campaignkey: str = typer.Argument(..., help="unique campaign key")
) -> None:
    campaign = EmailCampaign()
    campaigntype: Literal["normal", "abtesting"] = questionary.select(
        "What type of campaign do you want?", choices=["normal", "abtesting"]
    ).ask()
    campaign.single_campaigns(campaignkey, campaigntype)


@app.command("list")
def list_campaigns(
    fromindex: int = typer.Option(1, "--fromindex"),
    range: int = typer.Option(100, "--range"),
) -> None:
    campaign = EmailCampaign()
    kwargs = dict()

    status_choices = [
        "all",
        "all campaigns",
        "drafts",
        "scheduled",
        "inprogress",
        "sent",
        "stopped",
        "canceled",
        "tobereviewed",
        "reviewed",
        "paused",
        "intesting",
    ]

    sort = questionary.select(
        "Select sorting order:", choices=["asc", "desc"], default="asc"
    ).ask()

    status = questionary.checkbox(
        "Select all statuses that apply (Space to select, Enter to confirm):",
        choices=status_choices,
    ).ask()

    if fromindex:
        kwargs["fromindex"] = fromindex
    if range:
        kwargs["range"] = range

    kwargs["sort"], kwargs["status"] = sort, "|".join(status)

    campaign.list_campaigns(**kwargs)


@app.command("create")
def create_campaign():
    campaign = EmailCampaign()
    campaignname = questionary.text(
        "What is the name of the campaign you want to create?"
    ).ask()
    subject_name = questionary.text(
        "What is the email subject line for this campaign?"
    ).ask()
    list_details = questionary.text(
        "Enter the unique list key or identifier for your custom mailing list:"
    ).ask()
    content_url = questionary.text(
        "What is the content for what you want to send? Note: Ensure it is a URL or Link."
    ).ask()
    keys_list = [k.strip() for k in list_details.split(",") if k.strip()]
    campaign.create_campaign(
        campaign_name=campaignname,
        subject=subject_name,
        list_details=keys_list,
        content_url=content_url,
    )


@app.command("send", help="send a campaign immediately")
def send_campaign(
    campaignkey: str = typer.Argument(..., help="unique campaign key")
) -> None:
    campaign = EmailCampaign()
    list_details = questionary.text(
            "Enter the unique list key or identifier for your custom mailing list:"
        ).ask()
    if questionary.confirm(
        f"Are you sure you want to send campaign {campaignkey} now?", default=False
    ).ask():
        campaign.send_campaign(campaignkey, [list_details,])


@app.command("schedule", help="schedule a campaign to send at a future date/time")
def schedule_campaign(
    campaignkey: str = typer.Argument(..., help="unique campaign key")
) -> None:
    campaign = EmailCampaign()

    scheduledate = questionary.text("Enter the schedule date (mm/dd/yyyy):").ask()
    schedulehour = questionary.text("Enter the schedule hour (1-12):").ask()
    scheduleminute = questionary.text("Enter the schedule minute (00-55):").ask()
    am_pm: Literal["AM", "PM"] = questionary.select(
        "AM or PM?", choices=["AM", "PM"]
    ).ask()
    sendingtz = questionary.text(
        "Enter a recipient timezone (optional, e.g. Asia/Kolkata):"
    ).ask()

    campaign.schedule_campaign(
        campaignkey=campaignkey,
        scheduledate=scheduledate,
        schedulehour=schedulehour,
        scheduleminute=scheduleminute,
        am_pm=am_pm,
        sendingtz=sendingtz or None,
    )


@app.command("clone", help="clone an existing campaign")
def clone_campaign(
    oldcampaignkey: str = typer.Argument(..., help="campaign key to clone from")
) -> None:
    campaign = EmailCampaign()

    campaignname = questionary.text("Name for the cloned campaign:").ask()
    subject = questionary.text("Subject line for the cloned campaign:").ask()
    from_name = questionary.text("From name (optional):").ask()
    from_add = questionary.text("From email address (optional):").ask()
    reply_to = questionary.text("Reply-to email address (optional):").ask()

    campaign.clone_campaign(
        oldcampaignkey=oldcampaignkey,
        campaignname=campaignname,
        subject=subject,
        from_name=from_name or None,
        from_add=from_add or None,
        reply_to=reply_to or None,
    )


@app.command("reports", help="get the report summary for a campaign")
def campaign_reports(
    campaignkey: str = typer.Argument(..., help="unique campaign key")
) -> None:
    campaign = EmailCampaign()
    campaign.campaign_reports(campaignkey)


@app.command("recently-sent", help="view the most recently sent campaigns")
def recently_sent_campaigns() -> None:
    campaign = EmailCampaign()
    campaign.recently_sent_campaigns()


@app.command("last-report", help="get the report for the last sent campaign")
def last_campaign_report() -> None:
    campaign = EmailCampaign()
    campaign.last_campaign_report()


@app.command("recipients", help="get campaign recipients data by action type")
def campaign_recipients_data(
    campaignkey: str = typer.Argument(..., help="unique campaign key")
) -> None:
    action_choices = [
        "sentcontacts",
        "openedcontacts",
        "optoutcontacts",
        "spamcontacts",
        "unopenedcontacts",
        "clickedcontacts",
        "senthardbounce",
        "sentsoftbounce",
        "unsentcontacts",
    ]
    action = questionary.select(
        "Which set of recipients do you want?", choices=action_choices
    ).ask()

    campaign = EmailCampaign()
    campaign.campaign_recipients_data(campaignkey, action)


@app.command("coupon-details", help="view details for a coupon code")
def view_coupon_details(
    couponcode: str = typer.Argument(..., help="coupon code")
) -> None:
    campaign = EmailCampaign()
    campaign.view_coupon_details(couponcode)


@app.command("coupon-status", help="change a coupon's status (e.g. mark as used)")
def change_coupon_status(
    couponcode: str = typer.Argument(..., help="coupon code"),
    changestatus: str = typer.Option(
        "used", "--status", help="Status to set the coupon to"
    ),
) -> None:
    campaign = EmailCampaign()
    campaign.change_coupon_status(couponcode, changestatus)


@app.command("delete", help="delete a campaign using the campaign key")
def delete_campaign(
    campaignkey: str = typer.Argument(..., help="unique campaign key")
) -> None:
    if questionary.confirm(
        f"Are you sure you want to delete campaign {campaignkey}?", default=False
    ).ask():
        campaign = EmailCampaign()
        campaign.delete_campaign(campaignkey)
