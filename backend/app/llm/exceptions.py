"""Exceptions raised by the LLM client, mapped to HTTP statuses in the router."""


class LLMError(Exception):
    """Base class for all LLM integration errors."""


class LLMUnavailableError(LLMError):
    """The model could not be reached (connection refused, timeout, non-200)."""


class LLMResponseError(LLMError):
    """The model responded, but its output could not be parsed or used."""
