from rich import print
from rich.table import Table
from rich.panel import Panel


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
