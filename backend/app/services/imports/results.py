"""Shared result types for the import reconciliation layer."""

from dataclasses import dataclass
from enum import Enum


class ReconcileOutcome(Enum):
    """What happened when a single row (or fact) was reconciled against the DB."""

    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    SKIPPED_UNMATCHED = "skipped_unmatched"


class RowReconciliationError(Exception):
    """Raised when a single row can't be reconciled (e.g. an unrecognized value).

    Caught per-row by the orchestrator, not per-run, so one bad row doesn't
    fail the whole import.
    """


@dataclass
class MarksRowSummary:
    """Tally of what happened to the (up to 4) marks unpivoted from one wide
    UCT_MARKS/IT_TRANSCRIPTS row - there's no single ReconcileOutcome for a row
    that can contain several independent facts.
    """

    created: int = 0
    updated: int = 0
    unchanged: int = 0
    flagged: bool = False


def combine_outcomes(*outcomes: ReconcileOutcome) -> ReconcileOutcome:
    """Fold several per-entity outcomes (e.g. Applicant + Application from one
    ASR row) into a single outcome for counting purposes.
    """
    if ReconcileOutcome.SKIPPED_UNMATCHED in outcomes:
        return ReconcileOutcome.SKIPPED_UNMATCHED
    if ReconcileOutcome.CREATED in outcomes:
        return ReconcileOutcome.CREATED
    if ReconcileOutcome.UPDATED in outcomes:
        return ReconcileOutcome.UPDATED
    return ReconcileOutcome.UNCHANGED


@dataclass
class RunCounters:
    """Running tally of what an import run actually did, matching ImportRun's
    own row-count columns.
    """

    rows_rejected: int = 0
    rows_loaded: int = 0
    rows_auto_matched: int = 0
    rows_auto_new: int = 0
    rows_flagged: int = 0

    def add_outcome(self, outcome: ReconcileOutcome) -> None:
        """Fold one row-level (ASR/motivation) outcome into the running totals."""
        if outcome is ReconcileOutcome.CREATED:
            self.rows_loaded += 1
            self.rows_auto_new += 1
        elif outcome in (ReconcileOutcome.UPDATED, ReconcileOutcome.UNCHANGED):
            self.rows_loaded += 1
            self.rows_auto_matched += 1
        elif outcome is ReconcileOutcome.SKIPPED_UNMATCHED:
            self.rows_flagged += 1

    def add_marks_summary(self, summary: MarksRowSummary) -> None:
        """Fold one wide marks row's per-course results into the running totals.

        Counted at fact (per-mark) grain, not row grain: a wide row where 2 of
        4 marks changed and 2 didn't has no single accurate row-level answer.
        """
        if summary.flagged:
            self.rows_flagged += 1
            return
        self.rows_loaded += summary.created + summary.updated + summary.unchanged
        self.rows_auto_new += summary.created
        self.rows_auto_matched += summary.updated + summary.unchanged
