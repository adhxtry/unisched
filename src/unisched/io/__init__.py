"""
Input/output layer for tabular exam data ingestion and export.

This package handles file parsing and schema normalization before data is handed
to `unisched.core`. It should use pandas DataFrame as the transport format at
public boundaries.

Planned files and responsibilities:
- `readers/_base.py`
    - Shared reader protocol/ABC for tabular sources.
- `readers/_impl.py`
    - CSV parsing with delimiter/encoding handling.
    - Excel parsing (`.xls`, `.xlsx`) with sheet selection support.
    - ODS parsing for open document spreadsheets.
- `schema_mapper.py`
    - Map heterogeneous source columns into canonical schema names.
- `validator.py`
    - Structural checks for required columns, dtypes, and null policies.
- `normalizer.py`
    - Clean and standardize records into canonical DataFrame layout.
- `exporters.py`
    - Persist schedules and reports to CSV/Excel (and future formats).

Planned main classes/functions:
- `BaseReader`
- `CSVReader`
- `ExcelReader`
- `ODSReader`
- `read_input(...)`
- `normalize_input(df: DataFrame) -> DataFrame`
- `export_schedule(...)`
"""
