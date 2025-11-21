"""
Sensitive Data Logging Filter for Backend API.

Protects against exposure of:
- Passwords and authentication credentials
- JWT tokens
- User emails and PII
- Evidence content and case information
- API keys and secrets
"""

import re
import logging


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that sanitizes sensitive information before logging.

    Patterns detected and masked:
    - Passwords in error messages
    - JWT tokens (Bearer tokens, encoded JWTs)
    - User emails
    - Evidence content (Korean text in errors)
    - Case information
    - API keys and secrets
    """

    # Regex patterns for sensitive data
    PATTERNS = [
        # Passwords
        (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), r'password: ***'),
        (re.compile(r'Invalid password:\s*.+'), 'Invalid password: ***'),
        (re.compile(r'Wrong password:\s*.+'), 'Wrong password: ***'),

        # JWT Tokens
        (re.compile(r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}'), '***JWT_TOKEN***'),
        (re.compile(r'Bearer\s+[a-zA-Z0-9_-]+'), 'Bearer ***'),
        (re.compile(r'JWT decode failed for token:\s*.+'), 'JWT decode failed for token: ***'),

        # Email addresses
        (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '***@***.***'),
        (re.compile(r'User\s+[^\s]+@[^\s]+\s+not found', re.IGNORECASE), 'User ***@***.*** not found'),

        # Korean text (evidence content, case info)
        (re.compile(r'[\uac00-\ud7a3]{3,}'), '***'),

        # Evidence and case-related patterns
        (re.compile(r'Failed to process evidence:\s*.+'), 'Failed to process evidence: ***'),
        (re.compile(r'No access to case:\s*.+'), 'No access to case: ***'),
        (re.compile(r'Case\s+["\']?[^"\']+["\']?\s+not found'), 'Case *** not found'),

        # OpenAI API keys
        (re.compile(r'sk-proj-[a-zA-Z0-9]{48,}'), 'sk-proj-***'),
        (re.compile(r'sk-[a-zA-Z0-9]{48,}'), 'sk-***'),

        # AWS credentials
        (re.compile(r'AKIA[0-9A-Z]{16}'), 'AKIA***'),
        (re.compile(r'AWS_SECRET_ACCESS_KEY["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'AWS_SECRET_ACCESS_KEY: ***'),

        # Generic secret patterns
        (re.compile(r'secret["\']?\s*[:=]\s*["\']?([^"\'\s,}]{8,})', re.IGNORECASE), 'secret: ***'),
        (re.compile(r'api_key["\']?\s*[:=]\s*["\']?([^"\'\s,}]{8,})', re.IGNORECASE), 'api_key: ***'),
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

        # Sanitize extra fields (FastAPI adds these)
        if hasattr(record, '__dict__'):
            for key in ['error_id', 'code', 'path', 'method', 'traceback']:
                if key in record.__dict__:
                    value = record.__dict__[key]
                    if isinstance(value, str):
                        record.__dict__[key] = self._sanitize(value)

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
