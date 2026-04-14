from pathlib import Path

import pandas as pd
import pytest

from unisched.io.files import ValidatedFile
from unisched.io.loader import HallDataConfig, RegDataConfig, DataLoader


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
    loader = DataLoader()

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
    loader = DataLoader()

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
    loader = DataLoader()

    result = loader.load_registration_data(input_file)

    pd.testing.assert_frame_equal(result, expected)


def test_load_registration_data_rejects_unsupported_extension(tmp_path: Path) -> None:
    """Unknown file extensions should fail fast with a clear error."""

    input_path = tmp_path / "registration.txt"
    input_path.write_text("student_id,course\n1,math\n", encoding="utf-8")
    input_file = ValidatedFile.from_path(input_path)
    loader = DataLoader()

    with pytest.raises(ValueError, match="Unsupported registration file format"):
        loader.load_registration_data(input_file)


def test_load_registration_data_rejects_non_validated_file() -> None:
    """The loader should only accept a ValidatedFile boundary object."""

    loader = DataLoader()

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

    loader = DataLoader()

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
    loader = DataLoader()

    with pytest.raises(ValueError, match="Missing required registration columns"):
        loader.load_registration_data(
            input_file,
            RegDataConfig(student_id_col="sid", course_col="subject"),
        )


def test_load_registration_data_applies_normalizer(tmp_path: Path) -> None:
    """Configured normalizer should run before required-column validation."""

    input_path = tmp_path / "registration.csv"
    pd.DataFrame({"sid": [1], "unit": ["math"]}).to_csv(input_path, index=False)

    def normalize_columns(data_frame: pd.DataFrame) -> pd.DataFrame:
        return data_frame.rename(columns={"sid": "student_id", "unit": "course"})

    input_file = ValidatedFile.from_path(input_path)
    loader = DataLoader()

    result = loader.load_registration_data(
        input_file,
        RegDataConfig(normalizer=normalize_columns),
    )

    expected = pd.DataFrame({"student_id": [1], "course": ["math"]})
    pd.testing.assert_frame_equal(result, expected)


def test_load_hall_capacity_data_reads_csv(tmp_path: Path) -> None:
    """Hall capacity CSV inputs should load with configured default columns."""

    input_path = tmp_path / "halls.csv"
    expected = pd.DataFrame(
        {
            "hall": ["AB-1", "AB-2"],
            "capacity": [25, 40],
            "group": [3, 3],
        }
    )
    expected.to_csv(input_path, index=False)

    loader = DataLoader()
    input_file = ValidatedFile.from_path(input_path)

    result = loader.load_hall_capacity_data(input_file)

    pd.testing.assert_frame_equal(result, expected)


def test_load_hall_capacity_data_reads_excel_sheet(tmp_path: Path) -> None:
    """Hall capacity Excel inputs should support sheet selection."""

    input_path = tmp_path / "halls.xlsx"
    expected = pd.DataFrame(
        {
            "hall": ["L-1"],
            "capacity": [300],
            "group": [1],
        }
    )

    with pd.ExcelWriter(input_path, engine="openpyxl") as writer:
        pd.DataFrame({"ignore": [0]}).to_excel(writer, sheet_name="Sheet1", index=False)
        expected.to_excel(writer, sheet_name="Halls", index=False)

    loader = DataLoader()
    input_file = ValidatedFile.from_path(input_path)

    result = loader.load_hall_capacity_data(
        input_file,
        HallDataConfig(sheet_name="Halls"),
    )

    pd.testing.assert_frame_equal(result, expected)


def test_load_hall_capacity_data_reads_ods(tmp_path: Path) -> None:
    """Hall capacity ODS inputs should load through the ODS reader path."""

    input_path = tmp_path / "halls.ods"
    expected = pd.DataFrame(
        {
            "hall": ["AB-1"],
            "capacity": [25],
            "group": [3],
        }
    )
    expected.to_excel(input_path, index=False, engine="odf")

    loader = DataLoader()
    input_file = ValidatedFile.from_path(input_path)

    result = loader.load_hall_capacity_data(input_file)

    pd.testing.assert_frame_equal(result, expected)


def test_load_hall_capacity_data_rejects_missing_columns(tmp_path: Path) -> None:
    """Hall capacity loading should fail when configured columns are missing."""

    input_path = tmp_path / "halls.csv"
    pd.DataFrame({"hall": ["A"], "capacity": [10]}).to_csv(input_path, index=False)

    loader = DataLoader()
    input_file = ValidatedFile.from_path(input_path)

    with pytest.raises(ValueError, match="Missing required hall capacity columns"):
        loader.load_hall_capacity_data(input_file)


def test_load_hall_capacity_data_applies_normalizer(tmp_path: Path) -> None:
    """Hall capacity normalizer should run before required-column validation."""

    input_path = tmp_path / "halls.csv"
    pd.DataFrame({"hall": ["A"], "cap": [10], "grp": [0]}).to_csv(input_path, index=False)

    def normalize_hall_columns(data_frame: pd.DataFrame) -> pd.DataFrame:
        return data_frame.rename(
            columns={
                "hall": "hall",
                "cap": "capacity",
                "grp": "group",
            }
        )

    loader = DataLoader()
    input_file = ValidatedFile.from_path(input_path)

    result = loader.load_hall_capacity_data(
        input_file,
        HallDataConfig(normalizer=normalize_hall_columns),
    )

    expected = pd.DataFrame({"hall": ["A"], "capacity": [10], "group": [0]})
    pd.testing.assert_frame_equal(result, expected)


def test_load_hall_capacity_data_rejects_unsupported_extension(tmp_path: Path) -> None:
    """Unknown hall-capacity file extensions should fail fast."""

    input_path = tmp_path / "halls.txt"
    input_path.write_text("Hall Name,Capacity,Group\nA,10,1\n", encoding="utf-8")

    loader = DataLoader()
    input_file = ValidatedFile.from_path(input_path)

    with pytest.raises(ValueError, match="Unsupported hall capacity file format"):
        loader.load_hall_capacity_data(input_file)


def test_load_hall_capacity_data_rejects_non_validated_file() -> None:
    """Hall loader should only accept ValidatedFile boundary inputs."""

    loader = DataLoader()

    with pytest.raises(TypeError, match="ValidatedFile"):
        loader.load_hall_capacity_data("not-a-validated-file")  # type: ignore[arg-type]
