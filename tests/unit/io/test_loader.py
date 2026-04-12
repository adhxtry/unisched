from pathlib import Path

import pandas as pd
import pytest

from unisched.io.files import ValidatedFile
from unisched.io.loader import RegDataConfig, RegDataLoader


def test_load_registration_data_reads_csv(tmp_path: Path) -> None:
    """CSV inputs should load into the expected DataFrame."""

    input_path = tmp_path / "registration.csv"
    expected = pd.DataFrame(
        {
            "student_id": [1, 2],
            "course": ["math", "physics"],
        }
    )
    expected.to_csv(input_path, index=False)

    input_file = ValidatedFile.from_path(input_path)
    loader = RegDataLoader()

    result = loader.load_registration_data(input_file)

    pd.testing.assert_frame_equal(result, expected)


def test_load_registration_data_reads_excel(tmp_path: Path) -> None:
    """Excel inputs should load through the default sheet selection."""

    input_path = tmp_path / "registration.xlsx"
    expected = pd.DataFrame(
        {
            "student_id": [10, 11],
            "course": ["chemistry", "biology"],
        }
    )
    expected.to_excel(input_path, index=False)

    input_file = ValidatedFile.from_path(input_path)
    loader = RegDataLoader()

    result = loader.load_registration_data(input_file)

    pd.testing.assert_frame_equal(result, expected)


def test_load_registration_data_reads_ods(tmp_path: Path) -> None:
    """ODS inputs should load through the ODS reader path."""

    input_path = tmp_path / "registration.ods"
    expected = pd.DataFrame(
        {
            "student_id": [21, 22],
            "course": ["history", "art"],
        }
    )
    expected.to_excel(input_path, index=False, engine="odf")

    input_file = ValidatedFile.from_path(input_path)
    loader = RegDataLoader()

    result = loader.load_registration_data(input_file)

    pd.testing.assert_frame_equal(result, expected)


def test_load_registration_data_rejects_unsupported_extension(tmp_path: Path) -> None:
    """Unknown file extensions should fail fast with a clear error."""

    input_path = tmp_path / "registration.txt"
    input_path.write_text("student_id,course\n1,math\n", encoding="utf-8")
    input_file = ValidatedFile.from_path(input_path)
    loader = RegDataLoader()

    with pytest.raises(ValueError, match="Unsupported registration file format"):
        loader.load_registration_data(input_file)


def test_load_registration_data_rejects_non_validated_file() -> None:
    """The loader should only accept a ValidatedFile boundary object."""

    loader = RegDataLoader()

    with pytest.raises(TypeError, match="ValidatedFile"):
        loader.load_registration_data("not-a-validated-file")  # type: ignore[arg-type]


def test_load_registration_data_uses_configured_sheet_name_and_columns(
    tmp_path: Path,
) -> None:
    """Configured sheet names and custom columns should be honored."""

    input_path = tmp_path / "registration.xlsx"
    expected = pd.DataFrame(
        {
            "student_number": [101],
            "unit": ["statistics"],
        }
    )

    with pd.ExcelWriter(input_path, engine="openpyxl") as writer:
        pd.DataFrame({"ignore": [0]}).to_excel(writer, sheet_name="Sheet1", index=False)
        expected.to_excel(writer, sheet_name="Sheet2", index=False)

    input_file = ValidatedFile.from_path(input_path)

    loader = RegDataLoader()

    result = loader.load_registration_data(
        input_file,
        RegDataConfig(
            student_id_col="student_number",
            course_col="unit",
            sheet_name="Sheet2",
        ),
    )

    pd.testing.assert_frame_equal(result, expected)


def test_load_registration_data_rejects_missing_configured_columns(
    tmp_path: Path,
) -> None:
    """Missing configured columns should raise a validation error."""

    input_path = tmp_path / "registration.csv"
    pd.DataFrame({"student_id": [1], "course": ["math"]}).to_csv(input_path, index=False)

    input_file = ValidatedFile.from_path(input_path)
    loader = RegDataLoader()

    with pytest.raises(ValueError, match="Missing required registration columns"):
        loader.load_registration_data(
            input_file,
            RegDataConfig(student_id_col="sid", course_col="subject"),
        )
