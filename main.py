"""This program takes in a zip archive file containing CSV PIM data exports.
It then converts the CSV files to Excel xlsx files and archives them in a new zip file.
It then uploads the two zip files to the PPE-Analytics server."""

import argparse
import datetime
import time
import tomllib
import zipfile
from pathlib import Path
from tempfile import SpooledTemporaryFile
from typing import Any
from typing import List
from typing import Optional

import niquests as requests
from clint.textui.progress import Bar as ProgressBar
from requests_toolbelt import MultipartEncoder
from requests_toolbelt import MultipartEncoderMonitor

from ppe_analytics_upload.csv2xlsx import csv2xlsx_filelike
from ppe_analytics_upload.utils import extract_date_from_zipfile

__version__ = "0.1.1"


def main() -> None:
    """Main function."""
    start: int = time.monotonic_ns()
    parser = argparse.ArgumentParser(
        prog="ppeupload",
        description=__doc__,
    )
    parser.add_argument(
        "zip_archive",
        type=str,
        help="The path to the zip archive containing the CSV export files.",
    )
    parser.add_argument(
        "--upload-only",
        dest="upload_only",
        action="store_true",
        default=False,
        help="Upload the zip archive to the PPE-Analytics server, but do not convert. "
        "Assumes the conversion already happened and the inital upload try failed.",
    )
    parser.add_argument("--version", "-V", action="version", version=__version__)
    args: argparse.Namespace = parser.parse_args()
    if not args.zip_archive:
        raise SystemExit("No zip archive specified.")
    no_gui(args.zip_archive, args.upload_only)
    end: int = time.monotonic_ns()
    duration: int = end - start
    duration_us: float = duration / 1e3
    duration_timedelta = datetime.timedelta(microseconds=duration_us)
    print(f"Program took {duration_timedelta} to run.")


def no_gui(zip_archive: str | Path, upload_only: bool = False) -> None:
    """Process the zip archive in the terminal"""
    csv_zip: Path
    xlsx_zip: Path
    if isinstance(zip_archive, str):
        zip_archive = Path(zip_archive)
    if upload_only:
        if zip_archive.is_dir():
            # PPE-Analytics_fullexport_csv_20240607050701.zip
            csv_zip_files: Optional[List[Path]] = list(
                zip_archive.glob("PPE-Analytics_fullexport_csv_*.zip")
            )
            assert len(csv_zip_files) == 1, "More than one CSV archive file found."
            csv_zip: Path = csv_zip_files[0]
            # PPE-Analytics_fullexport_xlsx_20240607050701.zip
            xlsx_zip_files: Optional[List[Path]] = list(
                zip_archive.glob("PPE-Analytics_fullexport_xlsx_*.zip")
            )
            assert len(xlsx_zip_files) == 1, "More than one XLSX archive file found."
            xlsx_zip: Path = xlsx_zip_files[0]
        else:
            if "csv" in zip_archive.name:
                csv_zip = zip_archive
                xlsx_zip = (
                    zip_archive.parent
                    / f"{zip_archive.stem.replace('csv', 'xlsx')}.zip"
                )
            elif "xlsx" in zip_archive.name:
                xlsx_zip = zip_archive
                csv_zip = (
                    zip_archive.parent
                    / f"{zip_archive.stem.replace('xlsx', 'csv')}.zip"
                )
            else:
                raise SystemExit("No CSV or XLSX archive file found.")
    else:
        csv_zip, xlsx_zip = process_export(zip_archive)
    upload_to_ppe_analytics(csv_zip, xlsx_zip)


def upload_to_ppe_analytics(csv_zip: Path, xlsx_zip: Path) -> None:
    """Upload the csv and xlsx zip files to PPE-Analytics server"""
    ses = requests.Session(
        multiplexed=True,
    )
    config_path: Path = Path(__file__).parent / "config.toml"
    with config_path.open("rb") as config_file:
        config: dict[str, Any] = tomllib.load(config_file)
    csv_endpoint: str = config["server"]["csv_endpoint"]
    xlsx_endpoint: str = config["server"]["xlsx_endpoint"]
    ppe_api_key: str = config["server"]["PPEApiKey"]
    ses.headers["PPEApiKey"] = ppe_api_key

    print(f"Uploading {csv_zip.name} to PPE-Analytics server")
    # with csv_zip.open("rb") as csv_file:
    #     res = ses.post(
    #         csv_endpoint,
    #         files={"file": csv_file},
    #         stream=True,
    #         timeout=(10, 10 * 60),
    #     )
    #     if res.status_code != 200:
    #         raise SystemExit(f"Error uploading {csv_zip.name} to PPE-Analytics server")
    #     print(res.json())
    encoder = create_upload(csv_zip)
    callback = create_callback(encoder)
    monitor = MultipartEncoderMonitor(encoder, callback)
    # res = ses.post(
    #     csv_endpoint,
    #     data=monitor,  # type: ignore
    #     headers={"Content-Type": monitor.content_type},
    #     timeout=(120 * 60, 120 * 60),
    # )
    # if res.status_code != 200:
    #     print(f"{res.status_code}, {res.reason}")
    #     raise SystemExit(f"Error uploading {csv_zip.name} to PPE-Analytics server")
    # print(res.json())
    print(f"Uploading {xlsx_zip.name} to PPE-Analytics server")
    # with xlsx_zip.open("rb") as xlsx_file:
    #     res = ses.post(
    #         xlsx_endpoint,
    #         files={"file": xlsx_file},
    #         stream=True,
    #         timeout=(10, 10 * 60),
    #     )
    #     if res.status_code != 200:
    #         raise SystemExit(f"Error uploading {xlsx_zip.name} to PPE-Analytics server")
    #     print(res.json())
    encoder = create_upload(xlsx_zip)
    callback = create_callback(encoder)
    monitor = MultipartEncoderMonitor(encoder, callback)
    res = ses.post(
        xlsx_endpoint,
        data=monitor,  # type: ignore
        headers={"Content-Type": monitor.content_type},
        timeout=(420 * 60, 420 * 60),
    )
    if res.status_code != 200:
        print(f"{res.status_code}, {res.reason}")
        raise SystemExit(f"Error uploading {xlsx_zip.name} to PPE-Analytics server")
    print(res.json())


def create_callback(encoder):
    encoder_len = encoder.len
    bar = ProgressBar(expected_size=encoder_len, filled_char="=")

    def callback(monitor):
        bar.show(monitor.bytes_read)

    return callback


def create_upload(file_to_upload: Path):
    return MultipartEncoder(
        {
            "file": (
                file_to_upload.name,
                open(file_to_upload.as_posix(), "rb"),
                "text/plain",
            ),
        }
    )


def process_export(zip_archive: str | Path) -> tuple[Path, Path]:
    """Main function."""
    csv_zip: Path
    if isinstance(zip_archive, str):
        csv_zip = Path(zip_archive)
    else:
        csv_zip = zip_archive
    export_date: datetime.datetime = extract_date_from_zipfile(csv_zip)
    export_date_str: str = export_date.strftime("%Y%m%d%H%M%S")
    csv_zip_new_name: Path = (
        csv_zip.parent / f"PPE-Analytics_fullexport_csv_{export_date_str}.zip"
    )
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
    csv_zip = csv_zip.rename(csv_zip_new_name)
    return csv_zip, xlsx_zip_path


if __name__ == "__main__":
    main()
