"""Formatter service that delegates to the formatter module."""
from app.formatter.response import format_reply

class FormatterService:
    def format(self, payload: dict, result):
        return format_reply(payload, result)
