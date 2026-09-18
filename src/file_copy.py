"""Copy files from a source directory to a destination directory, grouped by extension."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from aiopath import AsyncPath
from aioshutil import copyfile

LOGGING_MESSAGES = {
    "missing_source_or_dest": "source and destination are required",
    "source_not_dir": "source is not a directory",
    "dest_not_dir": "destination is not a directory",
    "file_not_file": "file is not a file",
}


async def copy(
    source: str | Path | None, destination: str | Path | None = "./dist", limit: int = 5
) -> None:
    """Copy files from ``source`` into ``destination``, grouped by file extension.

    Each file is placed under a subdirectory named after its extension
    (for example ``.txt``). Files without an extension go into ``other``.
    When multiple files share the same basename, later copies are renamed
    to include their relative source directory.

    Args:
        source: Path to the source directory to copy from.
        destination: Path to an existing destination directory. Defaults to
            ``./dist``.
        limit: Limit the levels of directories to copy.

    Raises:
        ValueError: If ``source`` or ``destination`` is ``None``, or if either
            path is not an existing directory.
    """
    logger = logging.getLogger()
    if source is None or destination is None:
        logger.critical(LOGGING_MESSAGES["missing_source_or_dest"])
        raise ValueError(LOGGING_MESSAGES["missing_source_or_dest"])

    source_path = AsyncPath(source)
    destination_path = AsyncPath(destination)

    if not await source_path.is_dir():
        logger.critical(LOGGING_MESSAGES["source_not_dir"])
        raise ValueError(LOGGING_MESSAGES["source_not_dir"])

    if await destination_path.exists() and not await destination_path.is_dir():
        logger.critical(LOGGING_MESSAGES["dest_not_dir"])
        raise ValueError(LOGGING_MESSAGES["dest_not_dir"])

    logger.info("Starting reading contents of %s", source_path)
    files = await read_folder(source_path, limit)
    if not files:
        return

    await copy_files(files, destination_path, source_path)


async def map_file_to_directory(file: AsyncPath) -> str:
    """Return the destination subdirectory name for a file based on its extension.

    Args:
        file: Path to an existing file.

    Returns:
        The file's suffix (for example ``.txt``), or ``other`` if the file has
        no extension.

    Raises:
        ValueError: If ``file`` is not a regular file.
    """
    if not await file.is_file():
        logger = logging.getLogger()
        logger.critical(LOGGING_MESSAGES["file_not_file"])
        raise ValueError(LOGGING_MESSAGES["file_not_file"])

    extension = file.suffix
    return "other" if extension == "" else extension


async def map_file_to_path(
    original: AsyncPath,
    destination: AsyncPath,
    source: AsyncPath,
    preserve: bool,
) -> AsyncPath:
    """Build the destination path for a single file, including duplicates.

    Args:
        original: Absolute path of the source file.
        destination: Root destination directory.
        source: Root source directory, used when resolving relative paths for
            collision-safe names.
        preserve: If ``True``, embed the relative parent directory in the
            filename to avoid basename collisions.

    Returns:
        The full destination path under the extension subdirectory.
    """
    file_directory = await map_file_to_directory(original)
    if preserve:
        relative: AsyncPath = original.relative_to(await source.resolve())
        original_directory = str(relative.parent).replace(os.sep, "-")
        file_name = f"{original.stem} (from {original_directory}){original.suffix}"
    else:
        file_name = original.name
    return AsyncPath(destination) / file_directory / file_name


async def copy_file(
    file: AsyncPath, destination: AsyncPath, source: AsyncPath, preserve: bool
) -> None:
    """Encapsulates all async copying operations under one task.

    Args:
        file: Source file to copy.
        destination: Root destination directory.
        source: Root source directory, used when resolving collision-safe names.
        preserve: If ``True``, embed the relative parent directory in the
            destination filename.
    """
    new_path = await map_file_to_path(file, destination, source, preserve)
    await AsyncPath(new_path).parent.mkdir(parents=True, exist_ok=True)
    await copyfile(file, new_path)


async def copy_files(
    files: list[AsyncPath],
    destination: str | AsyncPath,
    source: str | AsyncPath,
) -> None:
    """Copying each source file to its destination path, handling basename collisions.

    The first file with a given basename keeps its original name. Subsequent
    files with the same basename are renamed to include their relative source
    directory.

    Args:
        files: Collected source file paths.
        destination: Root destination directory.
        source: Root source directory.

    Returns:
        A mapping from each original file path to its destination path.
    """
    base_names: dict[str, bool] = {}

    logger = logging.getLogger()

    logger.info("Copying %d files", len(files))

    copy_tasks = []
    for file in files:
        preserve = file.name in base_names
        base_names[file.name] = True
        copy_tasks.append(
            asyncio.create_task(copy_file(file, destination, source, preserve))
        )

    # У випадку порожнього tasks wait буде падати
    if not copy_tasks:
        logger.debug("No files to copy")
        return

    logger.debug("Copying has been scheduled")
    done, _ = await asyncio.wait(copy_tasks)
    for task in done:
        if exc := task.exception():
            logger.error(exc)
            continue
    logger.debug("Copying has been done")


async def read_file(child_path: AsyncPath) -> list[AsyncPath]:
    """Allows files be collected under the same API as directories

    Args:
        child_path: Path of a file found while scanning a folder.

    Returns:
        A one-item list with the resolved absolute path of ``child_path``.
    """
    return [await AsyncPath(child_path).resolve()]


async def read_folder(directory: str | AsyncPath, limit: int = -1) -> list[AsyncPath]:
    """Collect files from a directory recursively.

    Args:
        directory: Directory to scan.
        limit: Maximum number of levels of directories to scan.

    Returns:
        A list of resolved absolute paths for every file under ``directory``.
    """
    files: list[AsyncPath] = []
    if limit == 0:
        return files

    tasks = []

    logger = logging.getLogger()

    logger.debug("Preparing to read contents of %s at level %d", directory, limit)
    async for child in AsyncPath(directory).iterdir():
        if await child.is_dir():
            tasks.append(asyncio.create_task(read_folder(child, limit - 1)))
        else:
            tasks.append(asyncio.create_task(read_file(child)))

    # У випадку порожнього tasks wait буде падати
    if not tasks:
        logger.debug("No contents in %s at level %d", directory, limit)
        return files

    logger.debug("Reading %s contents at level %d", directory, limit)
    done, _ = await asyncio.wait(tasks)
    for task in done:
        if exc := task.exception():
            logger.error(exc)
            continue
        files.extend(task.result())
    logger.debug("Done reading %s contents at level %d", directory, limit)
    return files
