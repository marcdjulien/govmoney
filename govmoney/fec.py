import json
import os
import re
import requests
import xmltodict

from dateutil import parser
from urllib.parse import urljoin
from wget import download


BASE_URL = "https://www.fec.gov"

BASE_DATA_URL = urljoin(BASE_URL, "files/")

XML_FILE_PATH = BASE_DATA_URL

SCHD_NAME_REGEX = {
	"schda": r"bulk-downloads/{year}/indiv\d+.zip",
	"schdb": r"bulk-downloads/{year}/pas\d+.zip"
}

def base_schd_download(schd_type, out_dir, year, local_update_times, debug):
    print(
        "Downloading {} data {}".format(
            schd_type,
            f"from year {year}" if year is not None else ""
        )
    )

    # Fetch the XML with all file information
    print("Fetching filings XML...")
    resp = requests.get(XML_FILE_PATH)
    info = xmltodict.parse(resp.text)
    results = info["ListBucketResult"]["Contents"]
    
    # Filter entries by year
    year_filter = r"\d\d\d\d" if year is None else year
    name_regex = SCHD_NAME_REGEX[schd_type].format(year=year_filter)
    items = [
        item for item in results
        if re.match(name_regex, item.get("Key", ""))
    ]

    assert items, f"No data found: {resp.text}"
    print(f"Downloading {len(items)} file(s)")
    # Download each zip
    new_update_times = {}
    for item in items:
        # Create output filename
        file_url = urljoin(BASE_DATA_URL, item["Key"])
        dst = os.path.join(out_dir, item["Key"])
        dst = os.path.abspath(dst)

        # Check if the file needs to be updated
        remote_time = item["LastModified"]
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


def schda_download(out_dir, year, update_times, debug):
    return base_schd_download("schda", out_dir, year, update_times, debug)


def schdb_download(out_dir, year, update_times, debug):
    return base_schd_download("schdb", out_dir, year, update_times, debug)

schda = schda_download
schdb = schdb_download
