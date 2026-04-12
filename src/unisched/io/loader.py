"""Registration data loader for the ``unisched.io`` layer."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

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


class RegDataLoader:
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

        extension = input_file.extension

        if extension == ".csv":
            return self._validate_loaded_data(
                self._load_csv(input_file.path),
                active_config,
            )
        if extension in {".xlsx", ".xls"}:
            return self._validate_loaded_data(
                self._load_excel(input_file.path, active_config.sheet_name),
                active_config,
            )
        if extension == ".ods":
            return self._validate_loaded_data(
                self._load_ods(input_file.path, active_config.sheet_name),
                active_config,
            )

        raise ValueError(f"Unsupported registration file format: {extension or '<no extension>'}")
