#!/usr/bin/env python3

import subprocess

import pandas as pd


def main() -> None:
    data = pd.read_csv("fellowship.csv")
    i = 0

    for _, row in data.iterrows():
        i += 1
        if i < 2:
            continue
        first_name = (
            str(row["Firstname"]).strip() if pd.notna(row["Firstname"]) else ""
        )
        middle_name = (
            str(row["Middlename"]).strip() if pd.notna(row["Middlename"]) else ""
        )
        last_name = str(row["Lastname"]).strip() if pd.notna(row["Lastname"]) else ""

        name = " ".join(part for part in (first_name, middle_name, last_name) if part)

        email = str(row["Email"]).strip() if pd.notna(row["Email"]) else ""

        fellowship_id = str(row["Fellowship Number"]).strip() if pd.notna(row["Fellowship Number"]) else ""

        member_id = row["Member ID"]

        if not name or not email or not member_id:
            print(f"Skipping row {_}: missing name or email")
            continue

        command = [
            "uv",
            "run",
            "cison",
            "certificates",
            "fellowship",
            "create",
            "-f",
            name,
            "-e",
            email,
            "-i",
            fellowship_id,
            "-m",
            str(int(member_id)),
        ]

        # if pd.notna(member_id) and str(member_id).strip():
        #     command.append("--member-id")
        #     command.append(str(member_id).strip())

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
