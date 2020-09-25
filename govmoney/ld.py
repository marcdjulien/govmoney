import json
import os
import re
import requests

from dateutil import parser
from urllib.parse import urljoin
from wget import download
import zipfile

from .base import DataDownloader, FileInfo


class LdBaseDownloader(DataDownloader):

    BASE_URL = "https://disclosurespreview.house.gov/"

    BASE_DATA_URL = urljoin(BASE_URL, "data/")

    JSON_FILE_PATH = None

    NAME_FILTER = None

    PREFIX_PATH = None

    def __init__(self, out_dir, updated_times, data_type, debug=False, year=None):
        super().__init__(out_dir, updated_times, data_type=data_type, debug=debug)
        self.year = year

    def get_file_infos(self):
        # Fetch the JSON with all file information
        print("Fetching past filings JSON...")
        past_filings_json_url = urljoin(self.BASE_DATA_URL, self.JSON_FILE_PATH)
        resp = requests.get(past_filings_json_url)
        info = resp.json()

        # Filter entries by year
        year_filter = r"\d\d\d\d" if self.year is None else self.year
        name_regex = self.NAME_FILTER.format(year=year_filter)
        items = [
            item for item in info
            if re.match(name_regex, item.get("name", ""))
        ]

        assert items, f"No data found using {name_regex}: {resp.text}"

        return [
            FileInfo(name=item["file"],
                     remote_url= urljoin(urljoin(self.BASE_DATA_URL, self.PREFIX_PATH), item["file"]),
                     local_dir=self.PREFIX_PATH,
                     modified=re.match(name_regex, item["name"]).groups()[2])
            for item in items
        ]


class Ld1Downloader(LdBaseDownloader):
    JSON_FILE_PATH = "LD/LdSearchPastFilings.json"
    NAME_FILTER = r"({year})\s*(Registrations)\s*XML\s*\((.+)\)"
    PREFIX_PATH = "LD/"
    def __init__(self, out_dir, updated_times, year, debug):
        super().__init__(out_dir, updated_times, year=year, data_type="ld1", debug=debug)


class Ld2Downloader(LdBaseDownloader):
    JSON_FILE_PATH = "LD/LdSearchPastFilings.json"
    NAME_FILTER = r"({year})\s*([1234MY].+)\s*XML\s*\((.+)\)"
    PREFIX_PATH = "LD/"
    def __init__(self, out_dir, updated_times, year, debug):
        super().__init__(out_dir, updated_times, year=year, data_type="ld2", debug=debug)


class Ld203Downloader(LdBaseDownloader):
    JSON_FILE_PATH = "LC/LcSearchPastFilings.json"
    NAME_FILTER = r"({year})\s*([1234MY].+)\s*XML\s*\((.+)\)"
    PREFIX_PATH = "LC/"
    def __init__(self, out_dir, updated_times, year, debug):
        super().__init__(out_dir, updated_times, year=year, data_type="ld203", debug=debug)


def ld1(out_dir, updated_times, year, debug):
    return Ld1Downloader(out_dir, updated_times, year, debug).download()


def ld2(out_dir, updated_times, year, debug):
    return Ld2Downloader(out_dir, updated_times, year, debug).download()


def ld203(out_dir, updated_times, year, debug):
    return Ld203Downloader(out_dir, updated_times, year, debug).download()
