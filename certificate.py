#!/usr/bin/env python3

import subprocess

import pandas as pd


def main() -> None:
    data = pd.read_csv("preconference.csv")
    i = 0

    for _, row in data.iterrows():
        i += 1
        if i < 2:
            continue
        first_name = (
            str(row["FIRST_NAME"]).strip() if pd.notna(row["FIRST_NAME"]) else ""
        )
        middle_name = (
            str(row["MIDDLE_NAME"]).strip() if pd.notna(row["MIDDLE_NAME"]) else ""
        )
        last_name = str(row["LAST_NAME"]).strip() if pd.notna(row["LAST_NAME"]) else ""

        name = " ".join(part for part in (first_name, middle_name, last_name) if part)

        email = str(row["EMAIL"]).strip() if pd.notna(row["EMAIL"]) else ""
        member_id = row["MEMBER_ID"]

        if not name or not email:
            print(f"Skipping row {_}: missing name or email")
            continue

        command = [
            "uv",
            "run",
            "cison",
            "certificates",
            "preconference",
            "2026",
            name,
            email,
        ]

        if pd.notna(member_id) and str(member_id).strip():
            command.append("--member-id")
            command.append(str(member_id).strip())

        print(f"Command is {command}")
        try:
            result = subprocess.run(
                command,
                check=True,
                text=True,
                capture_output=True,
            )
            print(f"Sent for {name}")

            if result.stdout.strip():
                print(result.stdout.strip())

        except subprocess.CalledProcessError as exc:
            print(f"Failed for {name}: {exc.stderr or exc}")

    print("Done sending certificates.")


if __name__ == "__main__":
    main()
