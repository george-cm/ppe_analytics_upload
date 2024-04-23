# PPE Analytics Upload

This program takes in a zip archive file containing CSV PIM data exports. It then converts the CSV files to Excel xlsx files and archives them in a new zip file. It then uploads the two zip files to the PPE-Analytics server.

## Usage

```console
ppeupload <path_to_csv_zip_archive>
```

This will:

1. Extract the CSV files from the input zip archive
2. Convert each CSV file to XLSX format
3. Archive the XLSX files in a new zip file
4. Upload both the original CSV and new XLSX zip files to the PPE-Analytics server
5. The program expects the input CSV zip archive to be in the format exported from the PIM system.

It will extract the export date from one of the CSV filenames and use that date to name the output XLSX zip file.

The URLs for the PPE-Analytics upload endpoints are configured in config.toml.

## Requirements

- Python 3.12 but should work with 3.7+
- Required Python packages are listed in the pyproject.toml file.

## Building

To build a standalone executable, run:

```console
python build.py
```

This uses PyInstaller to bundle everything into an executable in the dist folder.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
