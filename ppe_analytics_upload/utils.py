"""Date utils module"""

import datetime
import re
import zipfile
from pathlib import Path


def extract_date_from_zipfile(zip_archive: Path) -> datetime.datetime:
    """Extract the date from a PIM export data zip file."""
    zip_arch = zipfile.ZipFile(zip_archive, "r")
    for csv_file in zip_arch.namelist():
        if csv_file.startswith("item_list_"):
            export_date: datetime.datetime = get_export_date_from_file(csv_file)
            return export_date
    raise ValueError(
        f"Cannot find item_list_*.csv to extract export date in {zip_archive}"
    )


def get_export_date_from_file(filename: str) -> datetime.datetime:
    """Get the export date from the filename of a PIM export data file.

    Parses the filename to extract the date in YYYYMMDDHHMMSS format. Handles
    both 12 digit and 14 digit date formats.

    Args:
        filepath (Path): Path to the PIM export data file.

    Returns:
        datetime: The export date parsed from the filename.

    Raises:
        ValueError: If no date can be parsed from the filename.
    """
    pattern = re.compile(r".*_(\d{12,14}).*\.csv")
    text_date_lst = pattern.findall(filename)
    if text_date_lst:
        text_date = text_date_lst[-1]
    else:
        raise ValueError(f"Cannot parse date from filename {filename}")
    if len(text_date) == 12:
        dt_format = "%y%m%d%H%M%S"
    elif len(text_date) == 14:
        dt_format = "%Y%m%d%H%M%S"
    else:
        raise ValueError(f"Cannot parse date from filename {filename}")
    return datetime.datetime.strptime(text_date, dt_format)
