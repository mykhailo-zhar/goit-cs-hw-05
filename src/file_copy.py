"""Copy files from a source directory to a destination directory, grouped by extension."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from aiopath import AsyncPath
from aioshutil import copyfile


async def copy_async(
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
    if source is None or destination is None:
        raise ValueError("source and destination are required")

    source_path = Path(source)
    destination_path = Path(destination)

    if not source_path.is_dir():
        raise ValueError("source is not a directory")

    if destination_path.exists() and not destination_path.is_dir():
        raise ValueError("destination is not a directory")

    files = await read_folder_async(source_path, limit)
    if not files:
        return

    await copy_files_async(files, destination_path, source_path)


def map_file_to_directory(file: Path) -> str:
    """Return the destination subdirectory name for a file based on its extension.

    Args:
        file: Path to an existing file.

    Returns:
        The file's suffix (for example ``.txt``), or ``other`` if the file has
        no extension.

    Raises:
        ValueError: If ``file`` is not a regular file.
    """
    if not file.is_file():
        raise ValueError("file is not a file")

    extension = file.suffix
    return "other" if extension == "" else extension


def map_file_to_path(
    original: Path,
    destination: str | Path,
    source: str | Path,
    preserve: bool,
) -> Path:
    """Build the destination path for a single file.

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
    file_directory = map_file_to_directory(original)
    if preserve:
        relative = original.relative_to(Path(source).resolve())
        original_directory = str(relative.parent).replace(os.sep, "-")
        file_name = f"{original.stem} (from {original_directory}){original.suffix}"
    else:
        file_name = original.name
    return Path(destination) / file_directory / file_name


async def copy_file(file: Path, new_path: Path):
    await AsyncPath(new_path).parent.mkdir(parents=True, exist_ok=True)
    await copyfile(file, new_path)


async def copy_files_async(
    files: list[Path],
    destination: str | Path,
    source: str | Path,
) -> dict[Path, Path]:
    """Map each source file to its destination path, handling basename collisions.

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

    copy_tasks = []
    for file in files:
        preserve = file.name in base_names
        base_names[file.name] = True
        new_file_path = map_file_to_path(file, destination, source, preserve)
        copy_tasks.append(copy_file(file, new_file_path))
    await asyncio.gather(*copy_tasks)


async def read_folder_async(directory: str | Path, limit: int = 5) -> list[Path]:
    """Collect files from a directory recursively.

    Args:
        directory: Directory to scan.
        limit: Maximum number of levels of directories to scan.

    Returns:
        A list of resolved absolute paths for every file under ``directory``.
    """
    files: list[Path] = []
    if limit == 0:
        return files

    tasks = []

    for child in Path(directory).iterdir():
        if child.is_dir():
            tasks.append(read_folder_async(child, limit - 1))
        else:
            files.append(child.resolve())

    for file_list in await asyncio.gather(*tasks):
        files.extend(file_list)
    return files
