"""Registration data loader for the ``unisched.io`` layer."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

from unisched.io.files import ValidatedFile

logger = logging.getLogger("unisched.io")


@dataclass(frozen=True, slots=True)
class RegDataConfig:
    """Configuration for registration data loading.

    Defaults:
    - `student_id_col`: "student_id"
    - `course_col`: "course"
    - `sheet_name`: None (use first sheet)
    """

    student_id_col: str = "student_id"  # Column name for student IDs
    course_col: str = "course"  # Column name for course names
    sheet_name: str | int | None = None  # Optional sheet name/index for Excel/ODS files
    normalizer: Callable[[pd.DataFrame], pd.DataFrame] | None = (
        None  # Optional function to normalize the loaded DataFrame (e.g., trim whitespace, standardize case)
    )


@dataclass(frozen=True, slots=True)
class HallDataConfig:
    """Configuration for exam-hall capacity data loading."""

    hall_col: str = "Hall Name"  # Column name for exam hall identifier
    capacity_col: str = "Capacity"  # Column name for hall capacity
    group_col: str = "Group"  # Column name for hall grouping
    sheet_name: str | int | None = None  # Optional sheet name/index for Excel/ODS files
    normalizer: Callable[[pd.DataFrame], pd.DataFrame] | None = (
        None  # Optional function to normalize loaded hall-capacity data
    )


class DataLoader:
    """Load registration data from validated input files."""

    def _load_csv(self, file_path: Path) -> pd.DataFrame:
        logger.info("Loading CSV registration data from %s", file_path)
        return pd.read_csv(file_path)

    def _load_excel(
        self,
        file_path: Path,
        sheet_name: str | int | None = None,
    ) -> pd.DataFrame:
        logger.info("Loading Excel registration data from %s", file_path)
        if sheet_name is None:
            return pd.read_excel(file_path)

        return pd.read_excel(file_path, sheet_name=sheet_name)

    def _load_ods(
        self,
        file_path: Path,
        sheet_name: str | int | None = None,
    ) -> pd.DataFrame:
        logger.info("Loading ODS registration data from %s", file_path)
        if sheet_name is None:
            return pd.read_excel(file_path, engine="odf")

        return pd.read_excel(file_path, engine="odf", sheet_name=sheet_name)

    def _validate_loaded_data(
        self,
        data_frame: pd.DataFrame,
        config: RegDataConfig,
    ) -> pd.DataFrame:
        required_columns = {config.student_id_col, config.course_col}
        missing_columns = required_columns - set(data_frame.columns)

        if missing_columns:
            missing_list = ", ".join(sorted(missing_columns))
            raise ValueError(f"Missing required registration columns: {missing_list}")

        return data_frame[[config.student_id_col, config.course_col]]

    def _validate_hall_data(
        self,
        data_frame: pd.DataFrame,
        config: HallDataConfig,
    ) -> pd.DataFrame:
        required_columns = {config.hall_col, config.capacity_col, config.group_col}
        missing_columns = required_columns - set(data_frame.columns)

        if missing_columns:
            missing_list = ", ".join(sorted(missing_columns))
            raise ValueError(f"Missing required hall capacity columns: {missing_list}")

        hall_data = data_frame[[config.hall_col, config.capacity_col, config.group_col]].copy()
        if hall_data[config.capacity_col].isnull().any():
            raise ValueError("Hall capacity data contains null capacity values")
        if hall_data[config.group_col].isnull().any():
            raise ValueError("Hall capacity data contains null group values")

        hall_data[config.capacity_col] = pd.to_numeric(
            hall_data[config.capacity_col], errors="raise"
        )
        hall_data[config.group_col] = pd.to_numeric(hall_data[config.group_col], errors="raise")

        if (hall_data[config.capacity_col] < 1).any():
            raise ValueError("Hall capacity must be >= 1")
        if (hall_data[config.group_col] < 0).any():
            raise ValueError("Hall group must be >= 0")

        hall_data[config.capacity_col] = hall_data[config.capacity_col].astype(int)
        hall_data[config.group_col] = hall_data[config.group_col].astype(int)

        return hall_data

    def _load_tabular_data(
        self,
        input_file: ValidatedFile,
        sheet_name: str | int | None,
        *,
        unsupported_message: str,
    ) -> pd.DataFrame:
        extension = input_file.extension

        if extension == ".csv":
            return self._load_csv(input_file.path)
        if extension in {".xlsx", ".xls"}:
            return self._load_excel(input_file.path, sheet_name)
        if extension == ".ods":
            return self._load_ods(input_file.path, sheet_name)

        raise ValueError(unsupported_message.format(extension=extension or "<no extension>"))

    def load_registration_data(
        self,
        input_file: ValidatedFile,
        config: RegDataConfig | None = None,
    ) -> pd.DataFrame:
        """
        Load registration data from a file, automatically detecting the file format.

        Args:
            input_file (ValidatedFile): The validated file object containing the registration data.
            config (RegDataConfig | None): The configuration for loading registration data. If None, defaults will be used.
        Returns:
            DataFrame: A pandas DataFrame containing the loaded registration data.
        """
        if not isinstance(input_file, ValidatedFile):
            raise TypeError("input_file must be a ValidatedFile instance")

        active_config = config or RegDataConfig()
        logger.info("Loading registration data from %s", input_file.path)

        loaded_data = self._load_tabular_data(
            input_file,
            active_config.sheet_name,
            unsupported_message=("Unsupported registration file format: {extension}"),
        )

        if active_config.normalizer is not None:
            loaded_data = active_config.normalizer(loaded_data)

        return self._validate_loaded_data(loaded_data, active_config)

    def load_hall_capacity_data(
        self,
        input_file: ValidatedFile,
        config: HallDataConfig | None = None,
    ) -> pd.DataFrame:
        """Load exam hall-capacity data from a validated tabular file."""

        if not isinstance(input_file, ValidatedFile):
            raise TypeError("input_file must be a ValidatedFile instance")

        active_config = config or HallDataConfig()
        logger.info("Loading hall capacity data from %s", input_file.path)

        loaded_data = self._load_tabular_data(
            input_file,
            active_config.sheet_name,
            unsupported_message=("Unsupported hall capacity file format: {extension}"),
        )

        if active_config.normalizer is not None:
            loaded_data = active_config.normalizer(loaded_data)

        return self._validate_hall_data(loaded_data, active_config)
