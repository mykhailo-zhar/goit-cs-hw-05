"""CLI for copying files grouped by extension."""

from __future__ import annotations

import argparse
import asyncio

from file_copy import copy_async


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
        help="Limit the number of directories to copy",
    )
    args = parser.parse_args()
    asyncio.run(copy_async(args.source, args.destination, args.limit))


if __name__ == "__main__":
    main()
