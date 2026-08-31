"""
Defines the base class that every sheet adapter inherits from
"""

from enum import Enum

import pandas as pd

from app.adapters.exceptions import AdapterValidationError
from app.adapters.validation.rules import ValidationRules


class BaseAdapter:

    input_columns: type[Enum]
    critical_columns: dict[Enum, list]
    output_columns: type[Enum]

    def __init__(self, sheet: pd.DataFrame):
        self._sheet = sheet

    def validate_input_columns(self) -> None:
        """
        Responsible for first-contact with the intake data, ensures data is correct type
        for expected file type  (deals with coloumn shape of file)
        """
        sheet_columns = self._sheet.columns

        missing = {
            column.value
            for column in self.input_columns
            if column.value not in sheet_columns
        }

        if missing:
            # log event
            raise ValueError(f"Missing required columns: {missing}")
            # do other logic

        self._sheet = self._sheet[[column.value for column in self.input_columns]]

    def determine_violations(self) -> dict[Enum, dict[ValidationRules, pd.Series]]:
        """
        Determines all violations in the inputed sheet defined by the critical columns
        Returns:
            A dictionary mapping each critical column to its validation rules
            and the corresponding violation masks.

        """

        all_violations = {}

        # checks if there are any missing values deemed important
        for critical_col in self.critical_columns:
            rules = self.critical_columns[critical_col]
            violations = {}

            for rule in rules:
                violations[rule] = self._validate_column(
                    col=self._sheet[critical_col.value], rule=rule
                )

            all_violations[critical_col] = violations

        return all_violations

    def separate_rows(self, violations: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Separates the input sheet into clean rows and rejected rows requriing review
        """

        masks = [
            mask
            for column_violations in violations.values()
            for mask in column_violations.values()
        ]

        flagged_mask = pd.concat(masks, axis=1).any(axis=1)
        clean = self._sheet[~flagged_mask]
        needs_review = self._sheet[flagged_mask]

        return clean, needs_review

    def format_for_database(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Formats the sheet into columns that can be written into the database
        """

        # convert enum object mapping to source table mapping
        mapping = {
            column.value: db_column for column, db_column in self.output_columns.items()
        }

        return df.rename(columns=mapping)

    def process(self) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
        """
        The main method for the adapter class
        Processes data through the injection pipeline
        """

        try:
            
            self.validate_input_columns()
            
        except ValueError as e:
            # raise instead of swallowing this: a bare None here used to break
            # any caller unpacking a 3-tuple, and an orchestrator needs a real
            # exception to reliably tell "this run failed" from "this run worked"
            raise AdapterValidationError(str(e)) from e

        violations = self.determine_violations()
        clean, needs_review = self.separate_rows(violations)
        clean = self.format_for_database(clean)

        return clean, needs_review, violations

    def _validate_column(self, col, rule):
        """
        Checks if a value in a single column violates a give rule

        Returns:
            mask (bool): a mask representing all the invalid values in the column i.e [123,"hello","world"] -> [0, 1, 1] for numeric violation
        """

        match rule:
            case ValidationRules.NON_NULL:
                return col.isna()

            case ValidationRules.NUMERIC:
                # get the inverse of values that are digits ignore any not null values since already handled
                return col.notna() & pd.to_numeric(col, errors="coerce").isna()
