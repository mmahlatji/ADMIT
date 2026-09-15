"""LLM integration for natural-language queries.

``client`` holds the LLM abstraction (Ollama backend + a mock), ``prompts``
builds the messages sent to the model, and ``exceptions`` defines the error
types the router maps to HTTP statuses.
"""
