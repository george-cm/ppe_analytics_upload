"""Main script to uplpad the data from PIM to PPE-Analytics server"""

import argparse
import datetime
import tomllib
import zipfile
from pathlib import Path
from tempfile import SpooledTemporaryFile

import niquests as requests

from ppe_analytics_upload.csv2xlsx import csv2xlsx_filelike
from ppe_analytics_upload.utils import extract_date_from_zipfile


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Upload PPE PIM data exports to PPE-Analytics server"
    )
    parser.add_argument(
        "zip_archive",
        type=str,
        help="The path to the zip archive containing the CSV export files.",
    )
    args = parser.parse_args()
    if not args.zip_archive:
        raise SystemExit("No zip archive specified.")
    no_gui(args.zip_archive)


def no_gui(zip_archive: str | Path) -> None:
    """Process the zip archive in the terminal"""
    csv_zip, xlsx_zip = process_export(zip_archive)
    # csv_zip = Path("PPE-Analytics_fullexport_csv_20240419100908.zip")
    # xlsx_zip = Path("PPE-Analytics_fullexport_xlsx_20240419100908.zip")
    upload_to_ppe_analytics(csv_zip, xlsx_zip)


def upload_to_ppe_analytics(csv_zip: Path, xlsx_zip: Path) -> None:
    """Upload the csv and xlsx zip files to PPE-Analytics server"""
    ses = requests.Session(multiplexed=True)
    with open("config.toml", "rb") as config_file:
        config = tomllib.load(config_file)
    csv_endpoint = config["server"]["csv_endpoint"]
    xlsx_endpoint = config["server"]["xlsx_endpoint"]
    ppe_api_key = config["server"]["PPEApiKey"]
    ses.headers["PPEApiKey"] = ppe_api_key

    print(f"Uploading {csv_zip.name} to PPE-Analytics server")
    with csv_zip.open("rb") as csv_file:
        res = ses.post(csv_endpoint, files={"file": csv_file})
        if res.status_code != 200:
            raise SystemExit(f"Error uploading {csv_zip.name} to PPE-Analytics server")
        print(res.json())
    print(f"Uploading {xlsx_zip.name} to PPE-Analytics server")
    with xlsx_zip.open("rb") as xlsx_file:
        res = ses.post(xlsx_endpoint, files={"file": xlsx_file})
        if res.status_code != 200:
            raise SystemExit(f"Error uploading {xlsx_zip.name} to PPE-Analytics server")
        print(res.json())


def process_export(zip_archive: str | Path) -> tuple[Path, Path]:
    """Main function."""
    if isinstance(zip_archive, str):
        csv_zip = Path(zip_archive)
    else:
        csv_zip = zip_archive
    export_date: datetime.datetime = extract_date_from_zipfile(csv_zip)
    export_date_str: str = export_date.strftime("%Y%m%d%H%M%S")
    csv_zip_new_name: str = f"PPE-Analytics_fullexport_csv_{export_date_str}.zip"
    xlsx_zip_path: Path = (
        csv_zip.parent / f"PPE-Analytics_fullexport_xlsx_{export_date_str}.zip"
    )
    xlsx_zip = zipfile.ZipFile(
        xlsx_zip_path,
        mode="w",
        compression=zipfile.ZIP_STORED,
    )
    with zipfile.ZipFile(csv_zip, "r") as csv_zip_zipfile:
        for csv_file in csv_zip_zipfile.infolist():
            file_size = csv_file.file_size
            if not csv_file.filename.endswith(".csv"):
                continue
            with SpooledTemporaryFile(
                mode="w+t", max_size=file_size, encoding="utf-8", newline=""
            ) as csvf, SpooledTemporaryFile(max_size=10 * file_size) as xlsxf:
                print(f"Converting {csv_file.filename}")

                csvf.write(csv_zip_zipfile.read(csv_file).decode("utf-8"))
                csvf.seek(0)
                csv2xlsx_filelike(
                    csvf,
                    xlsxf,
                    silent=True,
                )
                xlsxf.seek(0)
                xlsx_zip.writestr(
                    csv_file.filename.removesuffix(".csv") + ".xlsx", xlsxf.read()
                )
    csv_zip.rename(csv_zip_new_name)
    return csv_zip, xlsx_zip_path


if __name__ == "__main__":
    main()
