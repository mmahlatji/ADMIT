"""Reconciles adapter output (clean/needs-review rows from a spreadsheet) into
the database - the "incremental updates" piece: detecting what's new vs
already-on-file, and updating in place without touching decision fields.
"""
