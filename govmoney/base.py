from collections import namedtuple
import os
import requests
import zipfile

from dateutil import parser
from urllib.parse import urljoin
from wget import download


FileInfo = namedtuple("FileInfo", ["name", "remote_url", "local_dir", "modified"])


class DataDownloader(object):
    """Downloads raw data."""

    def __init__(self, out_dir, updated_times, data_type, debug=False):
        self.out_dir = out_dir
        self.updated_times = updated_times
        self.data_type = data_type
        self.debug = debug

    def download(self):
        new_update_times = {}

        raw_out_dir = os.path.join(self.out_dir, "raw", self.data_type)
        os.makedirs(raw_out_dir, exist_ok=True)

        file_infos =  self.get_file_infos()
        print(f"Downloading {len(file_infos)} file(s)")

        for fi in file_infos:
            # Create output filename
            dst = os.path.join(raw_out_dir, fi.local_dir, fi.name)
            dst = os.path.abspath(dst)

            # Check if the file needs to be updated
            if dst in self.updated_times:
                remote_update_time = parser.parse(fi.modified)
                local_update_time = parser.parse(self.updated_times[dst])
                if remote_update_time == local_update_time:
                    print(f"Skipping {fi.remote_url} since it hasn't changed")
                    continue

            # Create parent directories
            os.makedirs(os.path.dirname(dst), exist_ok=True)

            # Download the file
            print(f"\n{fi.remote_url} -> {dst} ...")
            if not self.debug:
                download(fi.remote_url, dst)
                final_dst = os.path.join(
                    self.out_dir, self.data_type, fi.local_dir, fi.name)
                with zipfile.ZipFile(dst, 'r') as zipf:
                    zipf.extractall(final_dst)

            new_update_times[dst] = fi.modified

        return new_update_times

    def get_file_infos(self):
        """Returns a list of FileInfo objects for this site."""
        raise NotImplemented


