"""
Sensitive Data Logging Filter for AI Worker.

Protects against exposure of:
- OpenAI API keys
- AWS credentials
- User evidence content
- IP addresses
- Other PII in log messages
"""

import re
import logging


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that sanitizes sensitive information before logging.

    Patterns detected and masked:
    - OpenAI API keys: sk-proj-..., sk-...
    - AWS credentials: AKIA...
    - IP addresses: IPv4 format
    - Evidence content: Korean text patterns in error messages
    """

    # Regex patterns for sensitive data
    PATTERNS = [
        # OpenAI API keys
        (re.compile(r'sk-proj-[a-zA-Z0-9]{48,}'), 'sk-proj-***'),
        (re.compile(r'sk-[a-zA-Z0-9]{48,}'), 'sk-***'),

        # AWS Access Keys
        (re.compile(r'AKIA[0-9A-Z]{16}'), 'AKIA***'),

        # IPv4 addresses
        (re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'), '***.***.***.**'),

        # Generic sensitive content patterns
        # Korean text in error messages (evidence content)
        (re.compile(r'[\uac00-\ud7a3]{3,}'), '***'),

        # Exception messages with user content
        (re.compile(r'Failed to parse: .+'), 'Failed to parse: ***'),
        (re.compile(r'Parse error at line \d+: .+'), 'Parse error at line ***: ***'),
        (re.compile(r'OpenAI API error with key .+:'), 'OpenAI API error: ***'),
        (re.compile(r'Error: .+ credentials invalid'), 'Error: *** credentials invalid'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Sanitize sensitive data from log record.

        Args:
            record: LogRecord to sanitize

        Returns:
            bool: Always True (allow all messages after sanitization)
        """
        # Sanitize the main log message
        record.msg = self._sanitize(str(record.msg))

        # Sanitize args if they exist
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._sanitize(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._sanitize(str(arg)) for arg in record.args)

        # Sanitize exception info if present
        if record.exc_info:
            # Get the exception value
            exc_type, exc_value, exc_tb = record.exc_info
            if exc_value:
                # Create new exception with sanitized message
                sanitized_msg = self._sanitize(str(exc_value))
                new_exc = type(exc_value)(sanitized_msg)
                # Replace exc_info with sanitized version
                record.exc_info = (exc_type, new_exc, exc_tb)
                # Also update exc_text if it was already formatted
                record.exc_text = None  # Force re-formatting with new exception

        return True

    def _sanitize(self, text: str) -> str:
        """
        Apply all sanitization patterns to text.

        Args:
            text: Text to sanitize

        Returns:
            str: Sanitized text with sensitive data masked
        """
        for pattern, replacement in self.PATTERNS:
            text = pattern.sub(replacement, text)
        return text
