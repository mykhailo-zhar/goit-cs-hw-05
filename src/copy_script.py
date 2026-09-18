"""CLI for copying files grouped by extension."""

from __future__ import annotations

import argparse
import asyncio
import logging

if __package__ == "src":
    from .file_copy import copy
    from .utility import configure_logger
else:
    from file_copy import copy
    from utility import configure_logger


def main() -> None:
    """Parse CLI arguments and run asynchronous copy grouped by extension."""
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
        default=-1,
        const=-1,
        nargs="?",
        help="Limit the number of directories to copy",
    )
    args = parser.parse_args()

    logger = logging.getLogger()
    configure_logger(logger)

    asyncio.run(copy(args.source, args.destination, args.limit))


if __name__ == "__main__":
    main()
