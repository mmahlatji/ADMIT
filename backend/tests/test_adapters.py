import pandas as pd
import pytest

from app.adapters.columns.asr import ASRInputColumn, ASR_OUTPUT_COLUMNS
from app.adapters.validation.rules import ValidationRules
from app.adapters.asr import ASRAdapter
from app.adapters.base import BaseAdapter


@pytest.fixture
def valid_sheet():
    return pd.DataFrame(
        {
            "Application Number": ["100001"],
            "Campus Id": ["123456"],
            "Employee Id": ["EMP001"],
            "Academic Program Code": ["CSC"],
            "Sex": ["M"],
            "Academic Plan 1": ["CSC-HONS"],
            "Academic Plan 2": [None],
            "Academic Career": ["hons"],
            "Application Date": [pd.Timestamp("2026-01-15")],
            "Choice": ["first"],
            "Admit Type": ["regular"],
            "Semester": ["first"],
            "Last Registration": [pd.Timestamp("2026-02-28")],
            "Application Term": [pd.Timestamp("2026-01-01")],
            "Previous Application Term": [None],
            "First Name": ["John"],
            "Last Name": ["Doe"],
            "Cell Phone": ["0821234567"],
            "Home Phone": [None],
            "Email Address": ["john.doe@example.com"],
            "Population Group": ["A"],
            "Birth Date": [pd.Timestamp("2000-01-01")],
            "Citizenship Residency": ["South Africa"],
            "Non SA Citizenship": [None],
            "Effective Date": [pd.Timestamp("2026-01-01")],
            "Program Action": ["ADMT"],
            "Program Reason": ["REG"],
            "Program Status": ["AC"],
        }
    )


def test_adapter_accepts_valid_data(valid_sheet):
    adapter = ASRAdapter(valid_sheet)

    adapter.validate_input_columns()

    assert len(adapter._sheet) == 1


def test_validate_input_columns_prunes_extra_columns(valid_sheet):
    valid_sheet["Unrelated Extra Column"] = ["unexpected_value"]
    adapter = ASRAdapter(valid_sheet)

    adapter.validate_input_columns()

    expected_cols = [col.value for col in ASRInputColumn]
    assert list(adapter._sheet.columns) == expected_cols


def test_validate_input_columns_missing_raises_error(valid_sheet):
    invalid_sheet = valid_sheet.drop(columns=[ASRInputColumn.CAMPUS_ID.value])
    adapter = ASRAdapter(invalid_sheet)

    with pytest.raises(ValueError) as exc_info:
        adapter.validate_input_columns()

    assert "Missing required columns" in str(exc_info.value)
    assert ASRInputColumn.CAMPUS_ID.value in str(exc_info.value)


def test_validate_column_non_null():
    adapter = BaseAdapter(pd.DataFrame())
    series = pd.Series(["CSC-HONS", None])  # Row 0 valid, Row 1 violates NON_NULL

    mask = adapter._validate_column(series, ValidationRules.NON_NULL)

    assert mask.tolist() == [False, True]


def test_validate_column_numeric():
    adapter = BaseAdapter(pd.DataFrame())
    # Row 0: valid numeric string, Row 1: invalid alpha, Row 2: None (ignored by NUMERIC rule)
    series = pd.Series(["100001", "APP_ALPHA", None])

    mask = adapter._validate_column(series, ValidationRules.NUMERIC)

    assert mask.tolist() == [False, True, False]


def test_determine_violations_flags_critical_column_rules(valid_sheet):

    invalid_sheet = valid_sheet.copy()
    invalid_sheet[ASRInputColumn.EMPLOYEE_ID.value] = None
    invalid_sheet[ASRInputColumn.ACADEMIC_PLAN1.value] = None

    # Row 0 is valid, Row 1 is invalid
    df = pd.concat([valid_sheet, invalid_sheet], ignore_index=True)

    adapter = ASRAdapter(df)
    violations = adapter.determine_violations()

    # Application Number rule checks
    assert ValidationRules.NON_NULL in violations[ASRInputColumn.EMPLOYEE_ID]

    # Academic Plan 1 rule checks
    assert ValidationRules.NON_NULL in violations[ASRInputColumn.ACADEMIC_PLAN1]
    assert violations[ASRInputColumn.ACADEMIC_PLAN1][
        ValidationRules.NON_NULL
    ].tolist() == [False, True]


def test_separate_rows_splits_by_flagged_masks(valid_sheet):
    # 4 rows, 1 clean 3 dirty
    df = pd.concat(
        [valid_sheet, valid_sheet, valid_sheet, valid_sheet], ignore_index=True
    )
    adapter = ASRAdapter(df)

    mock_violations = {
        ASRInputColumn.CAMPUS_ID: {
            ValidationRules.NON_NULL: pd.Series([False, True, False, True]),
            ValidationRules.NUMERIC: pd.Series([True, False, False, True]),
        }
    }

    clean, needs_review = adapter.separate_rows(mock_violations)

    assert len(clean) == 1
    assert len(needs_review) == 3
    assert clean.index.tolist() == [2]
    assert needs_review.index.tolist() == [0, 1, 3]


def test_format_for_database_renames_to_schema_fields(valid_sheet):
    adapter = ASRAdapter(valid_sheet)
    db_df = adapter.format_for_database(valid_sheet)

    # Verifies all mapped database target columns (e.g. application_number, campus_id) exist
    for target_col in ASR_OUTPUT_COLUMNS.values():
        assert target_col in db_df.columns


def test_process_separates_clean_and_rejected_data(valid_sheet):

    df = pd.concat(
        [valid_sheet, valid_sheet, valid_sheet, valid_sheet], ignore_index=True
    )
    df.loc[1, ASRInputColumn.CAMPUS_ID.value] = None
    df.loc[2, ASRInputColumn.APPLICATION_NUMBER.value] = "INVALID"

    adapter = ASRAdapter(df)
    clean, needs_review, violations = adapter.process()

    assert len(clean) == 3
    assert len(needs_review) == 1

    # Clean row must use DB schema column names (e.g. campus_id)
    assert ASR_OUTPUT_COLUMNS[ASRInputColumn.CAMPUS_ID] in clean.columns

    # Rejected row retains source sheet header (e.g. "Campus Id")
    assert ASRInputColumn.CAMPUS_ID.value in needs_review.columns
    assert ASRInputColumn.APPLICATION_NUMBER.value in needs_review.columns


def test_process_missing_required_column_fails_cleanly(valid_sheet, capsys):
    invalid_sheet = valid_sheet.drop(columns=[ASRInputColumn.CAMPUS_ID.value])
    adapter = ASRAdapter(invalid_sheet)

    result = adapter.process()
    captured = capsys.readouterr()

    assert result is None
    assert "Input validation failed:" in captured.out
