#!/usr/bin/env python3

from datetime import datetime


from rich import print
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from rich.columns import Columns
from rich.prompt import get_console


def display_user_details(data: dict[dict | list | str, str]) -> None:

    profile_table = Table(show_header=True, header_style="bold cyan", box=None)
    profile_table.add_column("Field", style="dim")
    profile_table.add_column("Value")
    profile_table.add_row(
        "Full Name",
        f"[bold]{data['last_name']}[/bold], {data['first_name']} {data['middle_name']}",
    )
    profile_table.add_row("Member ID", data["member_id"])
    profile_table.add_row("User ID", data["user_id"])
    profile_table.add_row("Join Date", data["Joined"])
    profile_table.add_row(
        "Status", "[green]Transiting[/green]" if data["is_transiting"] else "Regular"
    )

    # 2. Financials Table (Maps nested 'paid_fees')
    fees_table = Table(show_header=True, header_style="bold yellow", box=None)
    fees_table.add_column("Fee Type", style="dim")
    fees_table.add_column("Status", justify="center")

    for fee, paid in data["paid_fees"].items():
        status_label = "[green]✓ Paid[/green]" if paid else "[red]✗ Unpaid[/red]"
        fees_table.add_row(fee.replace("_", " ").title(), status_label)

    # 3. Certificate Eligibility Panel
    cert = data["certificate_validity"]
    eligibility_color = "green" if cert["eligible"] else "red"
    cert_text = (
        f"Status: [{eligibility_color}]"
        f"{'ELIGIBLE' if cert['eligible'] else 'INELIGIBLE'}[/{eligibility_color}]\n"
        f"Cutoff: [bold]{cert['applied_cutoff']}[/bold]\n"
        f"Reason: [italic]{cert['reason']}[/italic]"
    )

    # Render everything in a clean dashboard
    print(
        Panel(
            profile_table,
            title="[bold blue]Member Profile[/bold blue]",
            border_style="blue",
        )
    )
    print(
        Panel(
            fees_table,
            title="[bold yellow]Financial Ledger[/bold yellow]",
            border_style="yellow",
        )
    )
    print(
        Panel(
            cert_text,
            title="[bold green]Certificate Validity[/bold green]",
            border_style="green",
        )
    )


def display_all_mailing_list(response: dict) -> None:

    console = Console()
    table = Table(
        title="📧 Zoho Campaigns Mailing Lists",
        show_lines=True,
        header_style="bold cyan",
    )

    table.add_column("#", justify="right", style="yellow")
    table.add_column("Name", style="green")
    table.add_column("Contacts", justify="right")
    table.add_column("Owner")
    table.add_column("Public")
    table.add_column("Created")
    table.add_column("Status")
    table.add_column("List Key", style="magenta")

    for i, mailing_list in enumerate(response["list_of_details"], start=1):
        table.add_row(
            str(i),
            mailing_list["listname"],
            mailing_list["noofcontacts"],
            mailing_list["owner"],
            "✅" if mailing_list["is_public"] == "true" else "❌",
            mailing_list["date"],
            mailing_list["lockstatus"],
            mailing_list["listkey"],
        )

    console.print(table)


BAR_WIDTH = 30


def percentage_bar(percent: float, color: str = "green") -> Text:
    """Creates a horizontal percentage bar."""

    filled = int((percent / 100) * BAR_WIDTH)

    return Text(
        "█" * filled + "░" * (BAR_WIDTH - filled),
        style=color,
    )


def make_bar_chart(title: str, data: dict, color: str = "cyan") -> Table:
    table = Table(title=title, expand=True)

    table.add_column("Category")
    table.add_column("Chart")
    table.add_column("Value", justify="right")

    values = [int(v) for v in data.values()]

    maximum = max(values) if values else 1

    for key, value in sorted(
        data.items(),
        key=lambda x: int(x[1]),
        reverse=True,
    ):
        value = int(value)

        width = int((value / maximum) * BAR_WIDTH)

        table.add_row(
            key,
            f"[{color}]" + "█" * width,
            str(value),
        )

    return table


def display_single_campaign_details(data: dict) -> None:

    console = get_console()

    details = data["campaign-details"][0]

    report = data["campaign-reports"][0] if data.get("campaign-reports") else None

    mailing_lists = data.get("associated_mailing_lists", [])
    mailing = mailing_lists[0] if mailing_lists else {}

    sent_dt = (
        datetime.fromtimestamp(int(details["sent_time"]) / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if details.get("sent_time")
        else None
    )

    header = Table.grid(expand=True)

    header.add_column()
    header.add_column(justify="right")

    header.add_row(
        f"[bold cyan]{details['campaign_name']}[/bold cyan]",
        f"[bold green]{data['campaign_status'].upper()}[/bold green]",
    )

    console.print(Panel(header, border_style="cyan"))

    metadata = Table(show_header=False, box=None)

    metadata.add_row("Subject", details["email_subject"])
    metadata.add_row("Sender", details["email_from"])
    metadata.add_row("Reply-To", details["reply_to"])
    metadata.add_row("Sent", sent_dt)
    metadata.add_row("Editor", details["email_type"])
    metadata.add_row("Topic", details["topic_name"])

    mailing_table = Table(show_header=False, box=None)

    mailing_table.add_row(
        "List",
        mailing.get("listname", "-"),
    )

    mailing_table.add_row(
        "Status",
        mailing.get("liststatus", "-"),
    )

    mailing_table.add_row(
        "Subscribers",
        str(data.get("total_subscribers_count", 0)),
    )

    mailing_table.add_row(
        "Bounces",
        mailing.get("no_of_bounce", "0"),
    )

    mailing_table.add_row(
        "Unsubscribed",
        mailing.get("no_of_unsubcontacts", "0"),
    )

    console.print(
        Columns(
            [
                Panel(metadata, title="Campaign Metadata"),
                Panel(mailing_table, title="Mailing List"),
            ]
        )
    )

    if report:  # type: ignore
        perf = Table(
            title="Campaign Performance",
            expand=True,
        )

        perf.add_column("Metric")
        perf.add_column("Progress")
        perf.add_column("%", justify="right")

        perf.add_row(
            "Delivered",
            percentage_bar(float(report["delivered_percent"]), "green"),
            report["delivered_percent"] + "%",
        )

        perf.add_row(
            "Opened",
            percentage_bar(float(report["open_percent"]), "cyan"),
            report["open_percent"] + "%",
        )

        perf.add_row(
            "Clicked",
            percentage_bar(float(report["unique_clicked_percent"]), "yellow"),
            report["unique_clicked_percent"] + "%",
        )

        perf.add_row(
            "Bounce",
            percentage_bar(float(report["bounce_percent"]), "red"),
            report["bounce_percent"] + "%",
        )

        perf.add_row(
            "Spam",
            percentage_bar(float(report["spam_percent"]), "magenta"),
            report["spam_percent"] + "%",
        )

        perf.add_row(
            "Unsubscribe",
            percentage_bar(float(report["unsubscribe_percent"]), "red"),
            report["unsubscribe_percent"] + "%",
        )

        console.print(Panel(perf, border_style="green"))

        charts = Columns(
            [
                Panel(
                    make_bar_chart(
                        "Countries",
                        data["campaign-by-location"],
                        "green",
                    )
                ),
                Panel(
                    make_bar_chart(
                        "Browsers",
                        data["useragentstats"]["browsers_percent"],
                        "cyan",
                    )
                ),
            ],
            equal=True,
        )

        console.print(charts)

        devices = Columns(
            [
                Panel(
                    make_bar_chart(
                        "Computer",
                        data["useragentstats"]["computer_percent"],
                        "blue",
                    )
                ),
                Panel(
                    make_bar_chart(
                        "Mobile",
                        data["useragentstats"]["mobile_percent"],
                        "yellow",
                    )
                ),
                Panel(
                    make_bar_chart(
                        "Tablet",
                        data["useragentstats"]["tablets_percent"],
                        "magenta",
                    )
                ),
            ],
            equal=True,
        )

        console.print(devices)

    if report:  # type: ignore
        reach = data["campaign-reach"][0]

        reach_panel = Panel(
            make_bar_chart(
                "Campaign Reach",
                {
                    "Email": reach["emails"],
                    "Facebook": reach["facebook"],
                    "Twitter": reach["twitter"],
                    "LinkedIn": reach["linkedin"],
                    "Pinterest": reach["pinterest"],
                    "Tumblr": reach["tumblr"],
                    "Google+": reach["gplus"],
                },
                "bright_blue",
            ),
            border_style="bright_blue",
        )

        summary = Table(show_header=False)

        summary.add_row("Emails Sent", report["emails_sent_count"])
        summary.add_row("Delivered", report["delivered_count"])
        summary.add_row("Opened", report["opens_count"])
        summary.add_row("Unique Clicks", report["unique_clicks_count"])
        summary.add_row("Unopened", report["unopened"])
        summary.add_row("Click/Open Rate", report["clicksperopenrate"] + "%")
        summary.add_row("Soft Bounce", report["softbounce_count"])
        summary.add_row("Hard Bounce", report["hardbounce_count"])

        summary_panel = Panel(
            summary,
            title="Campaign Summary",
            border_style="magenta",
        )

        console.print(
            Columns(
                [
                    reach_panel,
                    summary_panel,
                ],
                equal=True,
            )
        )

    footer = Table.grid(expand=True)

    footer.add_column()
    footer.add_column(justify="right")

    footer.add_row(
        f"[dim]{data['url']} (v{data['version']})[/dim]",
        f"[dim]{data['status'].upper()} | Code {data['code']}[/dim]",
    )

    console.print(Panel(footer, border_style="dim"))


def display_all_campaigns(data: dict) -> None:

    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="right", ratio=1)

    status_color = "green" if data["status"] == "success" else "red"
    status_text = Text(
        f"Status: {data['status'].upper()}", style=f"bold {status_color}"
    )
    api_text = Text(f"URI: {data['uri']} (v{data['version']})", style="dim cyan")

    grid.add_row(status_text, api_text)

    table = Table(
        box=None, header_style="bold magenta", border_style="dim", expand=True
    )
    table.add_column("Name", style="bold white", width=12)
    table.add_column("Created Date", style="yellow", width=16, overflow="fold")
    table.add_column("Status", justify="center", width=10)
    table.add_column("Key (Truncated)", style="dim", width=30, overflow="fold")
    # table.add_column("Preview URL", style="blue underline", overflow="ellipsis")

    for camp in data["recent_campaigns"]:
        status_str = camp["campaign_status"]
        if status_str == "Draft":
            display_status = Text(status_str, style="bold yellow reverse")
        elif status_str == "Sent":
            display_status = Text(status_str, style="bold green reverse")
        else:
            display_status = Text(status_str, style="bold white reverse")

        truncated_key = camp["campaign_key"]

        table.add_row(
            camp["campaign_name"],
            camp["created_date_string"],
            display_status,
            truncated_key,
            # f"{camp['campaign_preview'][:14]}...",
        )

    console = get_console()

    console.print()
    console.print(Panel(grid, title="API RESPONSE METADATA", border_style="cyan"))
    console.print()
    console.print(Panel(table, title="RECENT CAMPAIGNS", border_style="magenta"))
    console.print()
