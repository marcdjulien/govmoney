import json
import re
import requests
import xmltodict

from urllib.parse import urljoin

from .base import DataDownloader, FileInfo

class ScheduleBaseDownloader(DataDownloader):

    BASE_URL = "https://www.fec.gov"

    BASE_DATA_URL = urljoin(BASE_URL, "files/")

    XML_FILE_PATH = BASE_DATA_URL

    FILE_FILTER = None

    def __init__(self, out_dir, updated_times, data_type, debug=False, year=None):
        super().__init__(out_dir, updated_times, data_type=data_type, debug=debug)
        self.year = year

    def get_file_infos(self):
        # Fetch the XML with all file information
        print("Fetching filings XML...")
        resp = requests.get(self.XML_FILE_PATH)
        info = xmltodict.parse(resp.text)
        results = info["ListBucketResult"]["Contents"]

        # Filter entries by year
        year_filter = r"\d\d\d\d" if self.year is None else self.year
        name_regex = self.FILE_FILTER.format(year=year_filter)
        items = [
            item for item in results
            if re.match(name_regex, item.get("Key", ""))
        ]
        assert items, f"No data found using {name_regex}: {resp.text}"

        return [
            FileInfo(name=item["Key"],
                     remote_url=urljoin(self.BASE_DATA_URL, item["Key"]),
                     local_dir="",
                     modified=item["LastModified"])
            for item in items
        ]


class ScheduleADownloader(ScheduleBaseDownloader):
    FILE_FILTER =  r"bulk-downloads/{year}/indiv\d+.zip",

    def __init__(self, out_dir, updated_times, year, debug):
        super().__init__(out_dir, updated_times, year=year, data_type="schda", debug=debug)


class ScheduleBDownloader(ScheduleBaseDownloader):
    FILE_FILTER =  r"bulk-downloads/{year}/pas\d+.zip"

    def __init__(self, out_dir, updated_times, year, debug):
        super().__init__(out_dir, updated_times, year=year, data_type="schdb", debug=debug)


def schda(out_dir, updated_times, year, debug):
    return ScheduleADownloader(out_dir, updated_times, year, debug).download()


def schdb(out_dir, updated_times, year, debug):
    return ScheduleBDownloader(out_dir, updated_times, year, debug).download()