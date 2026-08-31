"""Exceptions raised by the adapter layer."""


class AdapterValidationError(Exception):
    """Raised when an uploaded sheet is missing one or more required columns."""
