from pathlib import Path

import pytest

from unisched.io.files import ValidatedFile


def test_from_path_normalizes_to_absolute_path(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"

    validated_file = ValidatedFile.from_path(file_path)

    assert validated_file.path == file_path.resolve()
    assert str(validated_file) == str(file_path.resolve())
    assert file_path.exists()
    assert file_path.is_file()


def test_from_path_creates_parent_directories_and_file(tmp_path: Path) -> None:
    file_path = tmp_path / "nested" / "deeper" / "schedule.txt"

    validated_file = ValidatedFile.from_path(file_path)

    assert validated_file.path == file_path.resolve()
    assert file_path.exists()
    assert file_path.is_file()
    assert file_path.parent.exists()
    assert file_path.parent.is_dir()


def test_from_path_rejects_directory(tmp_path: Path) -> None:
    directory = tmp_path / "nested"
    directory.mkdir()

    with pytest.raises(IsADirectoryError):
        ValidatedFile.from_path(directory)
