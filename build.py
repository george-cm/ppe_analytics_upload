"""Build script for the project."""

import sys
from subprocess import run


def main():
    """Build the project."""
    # result = run(
    run(
        [
            "pyinstaller",
            "--add-data=./config.toml:.",
            "-n=ppeupload",
            "--additional-hooks-dir=.",
            "-y",
            "./main.py",
        ],
        capture_output=False,
        check=False,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    # print(result.stdout.decode())
    # print(result.stderr.decode())
    # print(result)


if __name__ == "__main__":
    # import timeit
    # from datetime import timedelta

    # print(str(timedelta(seconds=timeit.timeit(main, number=1))))
    main()
