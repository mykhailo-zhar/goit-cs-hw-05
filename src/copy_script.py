"""CLI for copying files grouped by extension."""

from __future__ import annotations

import argparse

from file_copy import copy


def main() -> None:
    parser = argparse.ArgumentParser(usage="copy.py [options]")
    parser.add_argument("-s", "--source", required=True, help="Source directory")
    parser.add_argument(
        "-d",
        "--destination",
        nargs="?",
        const="./dist",
        default="./dist",
        help="Destination directory",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=5,
        const=5,
        nargs="?",
        help="Limit the number of files to copy",
    )
    args = parser.parse_args()
    copy(args.source, args.destination, args.limit)


if __name__ == "__main__":
    main()
