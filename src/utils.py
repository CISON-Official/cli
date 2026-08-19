#!/usr/bin/env python3
import os
import sys
import time
import shutil
import contextlib
from pathlib import Path
from pdb import set_trace
from itertools import permutations
from typing import Any, Callable, Optional

import typer
import pandas as pd
from rich.live import Live
from rich.text import Text
from diskcache import Cache

from src.types import OutputFormat

USER_CACHE_DIR = Path.home() / ".cison" / ".cache"


def get_headers(token: str) -> dict:
    """Global headers like Authentication."""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def count_occurenance(data: dict) -> dict:
    counter: dict[str, int] = dict()
    for j in data:
        k = j.get("fees")
        if not (outstanding := k.get("unpaid")):
            print("continuing")
            continue
        for i in outstanding.keys():
            if not counter.get(i):
                counter[i] = 0
            counter[i] = counter[i] + 1
    return counter


def find_sub_combinations(data: list) -> dict[tuple, int]:
    counter: dict[tuple, int] = dict()

    for j in data:
        if not isinstance(j, dict):
            continue

        k = j.get("fees", {})
        if not k or not (outstanding := k.get("unpaid")):
            print("continue")
            continue

        current_perms = set(permutations(outstanding.keys()))
        existing_keys = set(counter.keys())
        matching_keys = existing_keys & current_perms

        if matching_keys:
            matched_key = list(matching_keys)[0]
            counter[matched_key] += 1
            continue

        new_key = list(current_perms)[0]
        counter[new_key] = 1

    return counter


def count_down(x: int) -> None:
    session = Live(transient=True, refresh_per_second=4)
    session.start()

    try:
        while x >= 0:
            hours = x // 3600
            minutes = (x % 3600) // 60
            seconds = x % 60

            time_format = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            display_text = Text(f"Time Remaining: {time_format}", style="bold cyan")

            session.update(display_text)
            time.sleep(1)
            x -= 1

    finally:
        session.stop()


def clean_nigerian_states(value):
    if (
        not isinstance(value, str)
        or value.strip() == ""
        or value.lower()
        in [
            "nil",
            "nigeria",
            "state",
            "09",
            "26",
            "042",
            "married",
            "hampshire",
            "georgia",
            "gauteng",
            "northern europe",
            "western",
        ]
    ):
        return "Unknown"

    val = value.strip().upper()

    mapping = {
        "AB": "Abia",
        "AD": "Adamawa",
        "AK": "Akwa Ibom",
        "Àkwa Ibom": "Akwa Ibom",
        "AQ": "Akwa Ibom",
        "AN": "Anambra",
        "BA": "Bauchi",
        "BY": "Bayelsa",
        "BE": "Benue",
        "BO": "Borno",
        "CR": "Cross River",
        "CRS": "Cross River",
        "DE": "Delta",
        "EB": "Ebonyi",
        "ED": "Edo",
        "EK": "Ekiti",
        "EN": "Enugu",
        "GO": "Gombe",
        "IM": "Imo",
        "JI": "Jigawa",
        "KD": "Kaduna",
        "KN": "Kano",
        "KT": "Katsina",
        "KE": "Kebbi",
        "KO": "Kogi",
        "KW": "Kwara",
        "LA": "Lagos",
        "NA": "Nasarawa",
        "NI": "Niger",
        "OG": "Ogun",
        "ON": "Ondo",
        "OS": "Osun",
        "OY": "Oyo",
        "PL": "Plateau",
        "RI": "Rivers",
        "SO": "Sokoto",
        "TA": "Taraba",
        "YO": "Yobe",
        "ZA": "Zamfara",
        "FC": "FCT",
        "FCT": "FCT",
    }

    fct_variants = [
        "ABUJA",
        "FEDERAL CAPITAL TERRITORY",
        "F.C.T",
        "F C T",
        "FDERAL CAPITAL TERITORY",
        "FCT",
        "Federal Capital",
    ]
    if any(x in val for x in fct_variants):
        return "FCT"

    if val in mapping:
        return mapping[val]

    if val.endswith(" STATE"):
        val = val.replace(" STATE", "")

    if val == "EBONY":
        val = "EBONYI"
    if val == "KOGI":
        val = "KOGI"

    return val.title()


def export_member_data_by_state(df: pd.DataFrame, state_column_name: str, dir="data"):
    """
    Cleans states, creates a directory, and saves filtered columns into state-specific CSVs.
    """
    main = "state"
    output_dir = f"{dir}/{main}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    target_cols = [
        "first_name",
        "middle_name",
        "last_name",
        "title",
        "member_id",
        "gender",
        "marital_status",
        "job_title",
        "phone_no",
    ]

    table = {"nigeria": clean_nigerian_states}

    for country in df.country.unique():
        demo_output = f"{output_dir}/{country}"
        os.makedirs(demo_output, exist_ok=True)
        print(f"Starting {country} ->")
        if clean_function := table.get(country.lower()):
            df["cleaned_state"] = df[state_column_name].apply(clean_function)

            for state, group in df.groupby("cleaned_state"):
                if state == "Unknown" or "-" in state:  # type: ignore
                    continue

                available_cols = [c for c in target_cols if c in group.columns]
                state_df = group[available_cols]

                file_name = f"{state.replace(' ', '_')}.csv"  # type: ignore
                file_path = os.path.join(demo_output, file_name)

                state_df.to_csv(file_path, index=False)
                print(f"\tSaved: {file_name}")

            print("Zipping ...")
            zip_directory(demo_output, f"cison_states_members_{country}")


def create_disk_cached_function(
    api_func: Callable[..., Any], cache_directory: str = "cison_dir"
) -> Callable[..., Any]:
    """Wraps any function with a persistent disk-backed cache stored in ~/.cison/.cache/."""
    cache_path = USER_CACHE_DIR / cache_directory
    cache_path.mkdir(parents=True, exist_ok=True)

    cache = Cache(str(cache_path))
    return cache.memoize(expire=5_000_000)(api_func)


def zip_directory(folder_to_zip: str, output_zip_filename: str):
    """
    Zips a target folder completely.

    :param folder_to_zip: Path to the folder you want to compress.
    :param output_zip_filename: Name of the output file (do not include '.zip').
    """
    shutil.make_archive(output_zip_filename, "zip", folder_to_zip)
    print(f"Successfully created: {output_zip_filename}.zip")


def convert_to_vcf(
    data: pd.DataFrame,
    root_dir: str,
    filename: str = "all_contacts.vcf",
    suffix="CISON",
) -> bool:
    """
    Combines an entire DataFrame of users into ONE single .vcf file
    that imports all contacts simultaneously when opened on a phone.
    """
    main_dir = os.path.join("data", "vcf", root_dir)

    os.makedirs(main_dir, exist_ok=True)

    output_file_path = os.path.join(main_dir, filename)

    try:
        #
        with open(output_file_path, "w", encoding="utf-8") as f:
            for row in data.itertuples(index=False):
                first = getattr(row, "first_name", "") or ""
                last = getattr(row, "last_name", "") or ""
                middle = getattr(row, "middle_name", "") or ""
                company = getattr(row, "company", "") or ""
                phone = getattr(row, "phone_no", "") or ""
                title = getattr(row, "title", "") or ""
                suffix = suffix if suffix else ""

                vcard_lines = [
                    "BEGIN:VCARD",
                    "VERSION:3.0",
                    f"N:{last};{first};{middle} {suffix};;",
                    f"FN:{first} {middle} {last} {suffix}".replace("  ", " ").strip(),
                    f"ORG:{company}",
                    f"TITLE:{title}",
                    f"TEL;TYPE=CELL;TYPE=VOICE:{phone}",
                    "END:VCARD",
                ]

                f.write("\n".join(vcard_lines) + "\n\n")

        print(f"Successfully created master VCF file at: {output_file_path}")
        return True

    except Exception as e:
        print(f"Error while creating master vcard: {e}")
        return False


@contextlib.contextmanager
def suppress_output():
    """Context manager to prevent any output to the terminal."""

    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def save_dataframe(
    data: dict | list,
    filename: Optional[str],
    default_name: str,
    output_format: OutputFormat,
) -> None:
    """Helper function to load data into a Pandas DataFrame and save to disk."""
    df = pd.DataFrame(data)

    # Determine base filename
    target_name = filename if filename else default_name

    # Ensure extension matches selected format
    base_path = Path(target_name).stem
    out_file = Path(f"{base_path}.{output_format.value}")

    # Export based on format
    if output_format == OutputFormat.csv:
        df.to_csv(out_file, index=False)
    elif output_format == OutputFormat.json:
        df.to_json(out_file, orient="records", indent=2)
    elif output_format == OutputFormat.xlsx:
        df.to_excel(out_file, index=False)
    elif output_format == OutputFormat.parquet:
        df.to_parquet(out_file, index=False)

    typer.secho(
        f"✓ Saved {len(df)} records to '{out_file.resolve()}'",
        fg=typer.colors.GREEN,
    )


USER_CACHE_DIR = Path.home() / ".cison" / ".cache"


def clear_disk_cache(sub_directory: str = None) -> int:  # type: ignore
    """
    Clears the disk cache directory.
    Returns the number of cleared directories/files.
    """
    if not USER_CACHE_DIR.exists():
        return 0

    target_dir = USER_CACHE_DIR / sub_directory if sub_directory else USER_CACHE_DIR

    if target_dir.exists():
        shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        return 1

    return 0
