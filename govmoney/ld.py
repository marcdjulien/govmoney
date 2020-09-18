import json
import os
import re
import requests

from dateutil import parser
from urllib.parse import urljoin
from wget import download


BASE_URL = "https://disclosurespreview.house.gov/"

BASE_DATA_URL = urljoin(BASE_URL, "data/")

LD_JSON_PATHS = {
    "ld1": "LD/LdSearchPastFilings.json",
    "ld2": "LD/LdSearchPastFilings.json",
    "ld203": "LC/LcSearchPastFilings.json"
}

LD_NAME_REGEX = {
    "ld1": r"({year})\s*([1234MY].+)\s*XML\s*\((.+)\)",
    "ld2": r"({year})\s*(Registrations)\s*XML\s*\((.+)\)",
    "ld203": r"({year})\s*([1234MY].+)\s*XML\s*\((.+)\)",
}

def base_ld_download(ld_type, out_dir, year, local_update_times, debug):
    print(
        "Downloading {} data {}".format(
            ld_type,
            f"from year {year}" if year is not None else ""
        )
    )

    # Fetch the JSON with all file information
    print("Fetching past filings JSON...")
    past_filings_json_url = urljoin(BASE_DATA_URL, LD_JSON_PATHS[ld_type])
    resp = requests.get(past_filings_json_url)
    info = resp.json()
    
    # Filter entries by year
    year_filter = r"\d\d\d\d" if year is None else year
    name_regex = LD_NAME_REGEX[ld_type].format(year=year_filter)
    items = [
        item for item in info 
        if re.match(name_regex, item.get("name", ""))
    ]

    assert items, f"No data found: {resp.text}"
    print(f"Downloading {len(items)} file(s)")
    # Download each zip
    new_update_times = {}
    prefix = "LD/" if ld_type in ["ld1", 'ld2'] else "LC/"
    for item in items:
        # Create output filename
        file_url = urljoin(urljoin(BASE_DATA_URL, prefix), item["file"])
        dst = os.path.join(out_dir, prefix, item["file"])
        dst = os.path.abspath(dst)

        # Check if the file needs to be updated
        _, _, remote_time = re.match(name_regex, item["name"]).groups()
        if dst in local_update_times:
            remote_update_time = parser.parse(remote_time)
            local_update_time = parser.parse(local_update_times[dst])
            if remote_update_time == local_update_time:
                print(f"Skipping {file_url} since it hasn't changed")
                continue

        # Create parent directories
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        # Download the file
        print(f"\n{file_url} -> {dst} ...")
        if not debug:
            download(file_url, dst)

        new_update_times[dst] = remote_time
    
    return new_update_times

def ld1_download(out_dir, year, update_times, debug):
    return base_ld_download("ld1", out_dir, year, update_times, debug)

def ld2_download(out_dir, year, update_times, debug):
    return base_ld_download("ld2", out_dir, year, update_times, debug)

def ld203_download(out_dir, year, update_times, debug):
    return base_ld_download("ld203", out_dir, year, update_times, debug)


ld1 = ld1_download
ld2 = ld2_download
ld203 = ld203_download
