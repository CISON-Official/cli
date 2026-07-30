#!/usr/bin/env python3

import sys
import typer

from src.gui.print import print_error_panel, print_warning_panel, print_info_panel


def handle_error(error_data: dict) -> None:
    """
    Evaluates campaign system API error codes using structural pattern matching
    and displays a styled diagnostic block to the terminal user.
    """
    error_code = error_data.get("code")
    # print(error_data)
    
    try:
        code_input = int(error_code)  # type: ignore
    except (ValueError, TypeError):
        code_input = 0

    match code_input:
        case 6601:
            title = "Access Denied"
            message = (
                "Your account permissions do not allow you to perform this action. "
                "Please verify your API token scope or contact your administrator."
            )
            print_error_panel(message=message, title=title)
            raise typer.Exit(1)

        case 6101:
            title = "Empty View"
            message = (
                "No campaign records exist inside this specific view. "
                "Check your filtering criteria, view IDs, or campaign status limits."
            )
            print_warning_panel(message=message, title=title)
            raise typer.Exit(0) 
        
        case 0:
            pass
        case 200:
            pass

        case _:
            title = "Unknown Error Code"
            print(error_data)
            message = (
                f"An unexpected or undocumented return condition occurred (Code: {error_code}). "
                "Verify the server connection or API documentation version."
            )
            print_info_panel(message=message, title=title)
            raise typer.Exit(1)

