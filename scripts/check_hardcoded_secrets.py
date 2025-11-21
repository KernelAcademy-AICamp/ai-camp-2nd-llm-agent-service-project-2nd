#!/usr/bin/env python3
"""
Hardcoded Secrets Detection Script

Scans the codebase for hardcoded sensitive values like:
- OpenAI API keys
- AWS credentials
- Database passwords
- JWT secrets
- Other API tokens

Returns exit code 1 if any secrets are found (for CI/CD)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class SecretMatch:
    """Represents a found secret"""
    file_path: str
    line_number: int
    line_content: str
    secret_type: str
    matched_value: str


# Regex patterns for detecting secrets
SECRET_PATTERNS = {
    "OpenAI API Key": re.compile(r'sk-[a-zA-Z0-9]{48,}'),
    "OpenAI Project Key": re.compile(r'sk-proj-[a-zA-Z0-9]{48,}'),
    "AWS Access Key": re.compile(r'AKIA[0-9A-Z]{16}'),
    "AWS Secret Key": re.compile(r'aws_secret_access_key\s*[=:]\s*["\']([^"\']{40})["\']', re.IGNORECASE),
    "Generic API Key": re.compile(r'api_key\s*[=:]\s*["\']([a-zA-Z0-9]{32,})["\']', re.IGNORECASE),
    "Database Password": re.compile(r'(password|passwd|pwd)["\']?\s*[=:]\s*["\'](?!{|<|test|example|password|changeme|secret)([^"\']{8,})["\']', re.IGNORECASE),
    "JWT Secret": re.compile(r'jwt_secret\s*[=:]\s*["\']([a-zA-Z0-9]{32,})["\']', re.IGNORECASE),
    "Private Key Header": re.compile(r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----'),
}

# Files and directories to exclude from scanning
EXCLUDE_PATTERNS = [
    r'\.git/',
    r'\.venv/',
    r'venv/',
    r'__pycache__/',
    r'node_modules/',
    r'\.pyc$',
    r'\.pyo$',
    r'\.md$',  # Markdown files (documentation)
    r'\.txt$',  # Text files
    r'\.json$',  # JSON files (might contain example configs)
    r'\.lock$',  # Lock files
    r'\.log$',  # Log files
    r'/tests?/fixtures/',  # Test fixture directories
    r'/examples?/',  # Example directories
    r'\.example$',  # Example files
    r'\.template$',  # Template files
    r'frontend/',  # Frontend code (client-side, different security model)
]

# Safe patterns that look like secrets but are actually placeholders/examples
# NOTE: These patterns should be strict to avoid false negatives
SAFE_PATTERNS = [
    r'your[_-]api[_-]key',
    r'your[_-]secret',
    r'<.*>',  # Placeholders like <YOUR_KEY>
    r'\{.*\}',  # Template variables like {API_KEY}
    r'xxx+',  # Masked values like xxxxx
    r'\*\*\*',  # Masked values like ***
    r'\.\.\.+',  # Ellipsis like ...
    r'\bexample\b',  # Word boundary for "example"
    r'\bsample\b',  # Word boundary for "sample"
    r'\bplaceholder\b',  # Word boundary for "placeholder"
]


def should_exclude_file(file_path: Path, base_path: Path) -> bool:
    """Check if file should be excluded from scanning"""
    relative_path = str(file_path.relative_to(base_path))
    # Normalize path separators for cross-platform compatibility
    relative_path = relative_path.replace('\\', '/')

    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, relative_path):
            return True

    return False


def is_safe_value(value: str) -> bool:
    """Check if matched value is actually a safe placeholder"""
    value_lower = value.lower()

    for pattern in SAFE_PATTERNS:
        if re.search(pattern, value_lower, re.IGNORECASE):
            return True

    return False


def scan_file(file_path: Path) -> List[SecretMatch]:
    """Scan a single file for hardcoded secrets"""
    matches = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            # Skip comments (Python and JavaScript style)
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue

            # Skip test/mock/fake variable assignments
            # e.g., fake_api_key = "...", mock_password = "...", test_secret = "...", sensitive_password = "..."
            line_lower = line.lower()
            if any(prefix in line_lower for prefix in ['fake_', 'mock_', 'test_', 'dummy_', 'example_', 'sample_', 'sensitive_']):
                continue

            # Check each secret pattern
            for secret_type, pattern in SECRET_PATTERNS.items():
                for match in pattern.finditer(line):
                    matched_value = match.group(0)

                    # Skip if it's a safe placeholder
                    if is_safe_value(matched_value):
                        continue

                    # Skip if the whole line context looks like a test/example
                    if is_safe_value(line):
                        continue

                    matches.append(SecretMatch(
                        file_path=str(file_path),
                        line_number=line_num,
                        line_content=line.strip(),
                        secret_type=secret_type,
                        matched_value=matched_value[:50] + '...' if len(matched_value) > 50 else matched_value
                    ))

    except Exception as e:
        print(f"Warning: Could not scan {file_path}: {e}", file=sys.stderr)

    return matches


def scan_directory(directory: Path) -> List[SecretMatch]:
    """Recursively scan directory for hardcoded secrets"""
    all_matches = []

    # File extensions to scan
    extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.sh', '.yml', '.yaml', '.env']

    for ext in extensions:
        for file_path in directory.rglob(f'*{ext}'):
            if should_exclude_file(file_path, directory):
                continue

            matches = scan_file(file_path)
            all_matches.extend(matches)

    return all_matches


def print_results(matches: List[SecretMatch]) -> None:
    """Print scan results in a readable format"""
    if not matches:
        print("[OK] No hardcoded secrets found!")
        return

    print(f"\n[WARNING] Found {len(matches)} potential hardcoded secret(s):\n")

    # Group by file
    by_file: Dict[str, List[SecretMatch]] = {}
    for match in matches:
        if match.file_path not in by_file:
            by_file[match.file_path] = []
        by_file[match.file_path].append(match)

    for file_path, file_matches in sorted(by_file.items()):
        print(f"[FILE] {file_path}")
        for match in file_matches:
            print(f"  Line {match.line_number}: {match.secret_type}")
            print(f"    {match.line_content}")
            print(f"    Matched: {match.matched_value}")
            print()


def main() -> int:
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scan for hardcoded secrets in codebase"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="Directory to scan (default: project root)"
    )

    args = parser.parse_args()

    # Determine scan directory
    if args.directory:
        scan_path = Path(args.directory).resolve()
    else:
        # Get project root (parent of scripts directory)
        script_dir = Path(__file__).parent
        scan_path = script_dir.parent

    if not scan_path.exists():
        print(f"Error: Directory not found: {scan_path}", file=sys.stderr)
        return 1

    print(f"Scanning for hardcoded secrets in: {scan_path}")
    print(f"Excludes: test fixtures, examples, templates, docs\n")

    matches = scan_directory(scan_path)
    print_results(matches)

    # Return exit code 1 if secrets found (for CI/CD)
    return 1 if matches else 0


if __name__ == "__main__":
    sys.exit(main())
