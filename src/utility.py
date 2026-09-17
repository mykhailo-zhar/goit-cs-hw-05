import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def get_files():
    """List regular files in the project ``data/`` directory.

    Returns:
        Paths of files under :data:`DATA_DIR`.
    """
    return [file_path for file_path in DATA_DIR.iterdir() if file_path.is_file()]


def get_formatter():
    """Return the shared log line format (time, name, thread, level, message).

    Returns:
        Formatter used by stream and file handlers.
    """
    return logging.Formatter(
        "%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s"
    )


def get_streamhandler(formatter: logging.Formatter):
    """Build a stdout handler at DEBUG level.

    Args:
        formatter: Formatter applied to emitted records.

    Returns:
        Stream handler writing to standard output.
    """
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    return stream_handler


def get_filehandler(formatter: logging.Formatter, prefix):
    """Build a timestamped file handler under ``logs/``.

    Args:
        formatter: Formatter applied to emitted records.
        prefix: Filename prefix, e.g. ``concurrent`` or ``parallel``.

    Returns:
        File handler writing to ``logs/{prefix}_search_{timestamp}.log``.
    """
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    tz = timezone(timedelta(hours=2))  # GMT+2
    timestamp = datetime.now(tz=tz).strftime("%Y%m%d_%H%M%S")
    log_filename = logs_dir / f"{prefix}_search_{timestamp}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    return file_handler


def configure_logger(logger: logging.Logger, prefix="concurrent"):
    """Attach stdout and file handlers to ``logger``.

    Args:
        logger: Logger to configure.
        prefix: Prefix for the log filename created by :func:`get_filehandler`.
    """
    formatter = get_formatter()

    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_streamhandler(formatter))
    logger.addHandler(get_filehandler(formatter, prefix))
