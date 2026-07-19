from __future__ import annotations

from pathlib import Path

import pytest

from src.file_copy import copy


def create_source_dir(tmp_dir: Path) -> Path:
    dir_name = tmp_dir / "source"
    dir_name.mkdir()
    return dir_name


def create_destination_dir(tmp_dir: Path) -> Path:
    dir_name = tmp_dir / "destination"
    return dir_name


def create_file(dir_name: Path, file_name: str, permissions: int = 0o644) -> Path:
    file = dir_name / file_name
    file.write_text("test")
    file.chmod(permissions)
    return file


def get_file_extname_dir(directory: Path, file: str) -> Path:
    return directory / Path(file).suffix


def count_files(dir_path: Path, extension: str) -> int:
    return sum(
        1 for file in (dir_path / extension).glob(f"*{extension}") if file.is_file()
    )


class TestCopy:
    def test_raises_when_source_and_destination_absent(self) -> None:
        with pytest.raises(TypeError):
            copy()  # type: ignore[call-arg]

    def test_raises_when_source_is_a_file(self, tmp_path: Path) -> None:
        temp_file = create_file(tmp_path, "test.txt")
        with pytest.raises(ValueError):
            copy(temp_file, "./dist")

    def test_raises_when_source_directory_does_not_exist(self) -> None:
        with pytest.raises(ValueError):
            copy("not_a_directory", "./dist")

    def test_raises_when_destination_is_a_file(self, tmp_path: Path) -> None:
        source_dir = create_source_dir(tmp_path)
        destination_file = create_file(tmp_path, "destination.txt")
        with pytest.raises(ValueError):
            copy(source_dir, destination_file)

    def test_copies_one_file_under_same_extension(self, tmp_path: Path) -> None:
        source_dir = create_source_dir(tmp_path)
        destination_dir = create_destination_dir(tmp_path)
        file_name = "test.txt"
        create_file(source_dir, file_name)

        copy(source_dir, destination_dir)

        assert get_file_extname_dir(destination_dir, file_name).is_dir()

    def test_copies_multiple_files_under_same_extension(self, tmp_path: Path) -> None:
        source_dir = create_source_dir(tmp_path)
        destination_dir = create_destination_dir(tmp_path)
        a_dir = source_dir / "a"
        b_dir = source_dir / "b"
        a_dir.mkdir()
        b_dir.mkdir()
        create_file(a_dir, "test.txt")
        create_file(b_dir, "test_2.txt")
        create_file(a_dir, "test.js")
        create_file(b_dir, "test.js")

        copy(source_dir, destination_dir)

        assert count_files(destination_dir, ".js") == 2
        assert count_files(destination_dir, ".txt") == 2
