"""Copy files from a source directory to a destination directory, grouped by extension."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def copy(
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

    files = collect_files(source_path, limit)
    if not files:
        return

    mapped_files = map_files(files, destination_path, source_path)
    create_directories(mapped_files.values())

    for original, mapped in mapped_files.items():
        shutil.copy2(original, mapped)


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


def create_directories(directories: list[Path]) -> None:
    """Create extension-based subdirectories under ``destination`` for ``files``.

    Args:
        directories: Directories to create.
    """
    parents = {directory.parent for directory in directories}
    for parent in parents:
        parent.mkdir(parents=True, exist_ok=True)


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


def map_files(
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
    mapped_files: dict[Path, Path] = {}
    base_names: dict[str, bool] = {}
    for file in files:
        preserve = file.name in base_names
        base_names[file.name] = True
        mapped_files[file] = map_file_to_path(file, destination, source, preserve)
    return mapped_files


def collect_files(directory: str | Path, limit: int = 5) -> list[Path]:
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
    for child in Path(directory).iterdir():
        if child.is_dir():
            files.extend(collect_files(child, limit - 1))
        else:
            files.append(child.resolve())
    return files
