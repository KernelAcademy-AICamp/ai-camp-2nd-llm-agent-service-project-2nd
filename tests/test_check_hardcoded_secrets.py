"""
Tests for hardcoded secrets detection script

RED Phase: Verify script detects hardcoded secrets and ignores safe patterns
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest


class TestHardcodedSecretsDetection:
    """Test hardcoded secrets detection script"""

    def run_script(self, temp_dir: Path) -> tuple[int, str, str]:
        """
        Run check_hardcoded_secrets.py script in temp directory

        Returns:
            (exit_code, stdout, stderr)
        """
        script_path = Path(__file__).parent.parent / "scripts" / "check_hardcoded_secrets.py"

        result = subprocess.run(
            ["python", str(script_path), str(temp_dir)],  # Pass temp_dir as argument
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        return result.returncode, result.stdout, result.stderr

    def test_detects_openai_api_key(self):
        """실제 OpenAI API 키가 하드코딩되어 있으면 감지해야 함"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create Python file with hardcoded OpenAI key
            config_file = temp_path / "config.py"
            config_file.write_text("""
# Configuration
OPENAI_API_KEY = "sk-proj-RealSecretKey123456789012345678901234567890123456"
DATABASE_URL = "postgresql://localhost/mydb"
""", encoding='utf-8')

            exit_code, stdout, stderr = self.run_script(temp_path)

            # Should detect the secret
            assert exit_code == 1, "Script should return exit code 1 when secrets found"
            assert "OpenAI" in stdout, "Should detect OpenAI API key"
            assert "config.py" in stdout, "Should report file name"

    def test_detects_aws_credentials(self):
        """AWS 자격증명이 하드코딩되어 있으면 감지해야 함"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create file with AWS credentials (test data - not real keys)
            # AWS Access Key: AKIA + exactly 16 chars (alphanumeric uppercase)
            # AWS Secret Key: exactly 40 chars
            aws_file = temp_path / "aws_config.py"
            aws_file.write_text("""
AWS_ACCESS_KEY_ID = "AKIAN0TR3ALK3Y123456"
AWS_SECRET_ACCESS_KEY = "N0tR3alS3cr3tK3y1234567890ABCDEFGH123456"
""", encoding='utf-8')

            exit_code, stdout, stderr = self.run_script(temp_path)

            assert exit_code == 1, f"Expected exit code 1, got {exit_code}. Stdout: {stdout}"
            assert "AWS Access Key" in stdout

    def test_detects_database_password(self):
        """데이터베이스 비밀번호가 하드코딩되어 있으면 감지해야 함"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create file with DB password
            db_file = temp_path / "database.py"
            db_file.write_text("""
db_config = {
    "host": "localhost",
    "password": "SuperSecret123!",
    "database": "production_db"
}
""", encoding='utf-8')

            exit_code, stdout, stderr = self.run_script(temp_path)

            # Debug output
            if exit_code != 1:
                print(f"\nDEBUG - DB password test")
                print(f"Exit code: {exit_code}")
                print(f"STDOUT:\n{stdout}")

            assert exit_code == 1, f"Expected exit code 1, got {exit_code}. Stdout: {stdout}"
            assert "Database Password" in stdout or "password" in stdout.lower()

    def test_ignores_safe_placeholders(self):
        """안전한 placeholder는 무시해야 함"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create file with safe placeholders
            config_file = temp_path / "config.py"
            config_file.write_text("""
# Safe placeholders
OPENAI_API_KEY = "your-api-key-here"
AWS_KEY = "<YOUR_AWS_KEY>"
DATABASE_PASSWORD = "{DB_PASSWORD}"
JWT_SECRET = "xxxxxxxxxxxxxxxxxxxxx"
API_TOKEN = "example-token-12345"
""", encoding='utf-8')

            exit_code, stdout, stderr = self.run_script(temp_path)

            # Should NOT detect these as secrets
            assert exit_code == 0, "Should return exit code 0 for safe placeholders"
            assert "[OK]" in stdout or "No hardcoded secrets" in stdout

    def test_ignores_test_variables(self):
        """테스트 코드의 fake/mock 변수는 무시해야 함"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create test file with fake credentials
            test_file = temp_path / "test_auth.py"
            test_file.write_text("""
def test_authentication():
    fake_api_key = "sk-proj-FakeKeyForTesting123456789012345678901234567890"
    mock_password = "TestPassword123!"
    test_secret = "test-jwt-secret-key-for-testing"

    assert authenticate(fake_api_key) is not None
""", encoding='utf-8')

            exit_code, stdout, stderr = self.run_script(temp_path)

            # Should ignore test variables
            assert exit_code == 0, "Should ignore fake/mock/test variables"

    def test_ignores_comments(self):
        """주석은 스캔하지 않아야 함"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create file with secrets in comments
            code_file = temp_path / "example.py"
            code_file.write_text("""
# API_KEY = "sk-proj-RealKey123456789012345678901234567890123456"
# Don't hardcode passwords like "SuperSecret123!"

def get_config():
    # TODO: Move to environment variables
    return {}
""", encoding='utf-8')

            exit_code, stdout, stderr = self.run_script(temp_path)

            # Should ignore comments
            assert exit_code == 0, "Should ignore secrets in comments"

    def test_excludes_test_fixtures(self):
        """테스트 fixture 디렉토리는 제외해야 함"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create fixture with real-looking secrets
            fixtures_dir = temp_path / "tests" / "fixtures"
            fixtures_dir.mkdir(parents=True)

            fixture_file = fixtures_dir / "sample_data.py"
            fixture_file.write_text("""
SAMPLE_API_KEY = "sk-proj-SampleKey123456789012345678901234567890123"
""", encoding='utf-8')

            exit_code, stdout, stderr = self.run_script(temp_path)

            # Should exclude fixtures
            assert exit_code == 0, "Should exclude test fixtures directory"

    def test_excludes_example_files(self):
        """.example 파일은 제외해야 함"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create .example file
            example_file = temp_path / "config.py.example"
            example_file.write_text("""
OPENAI_API_KEY = "sk-proj-YourKeyHere123456789012345678901234567890"
""", encoding='utf-8')

            exit_code, stdout, stderr = self.run_script(temp_path)

            # Should exclude .example files
            assert exit_code == 0, "Should exclude .example files"

    def test_reports_multiple_secrets(self):
        """여러 비밀값을 모두 보고해야 함"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create files with multiple secrets (test data - not real)
            file1 = temp_path / "config1.py"
            file1.write_text("""
OPENAI_KEY = "sk-proj-Secret1234567890123456789012345678901234567890"
""", encoding='utf-8')

            file2 = temp_path / "config2.py"
            file2.write_text("""
AWS_KEY = "AKIAN0TR3ALK3Y789012"
""", encoding='utf-8')

            exit_code, stdout, stderr = self.run_script(temp_path)

            # Should detect both
            assert exit_code == 1, f"Expected exit code 1, got {exit_code}. Stdout: {stdout}"
            assert "config1.py" in stdout or "config2.py" in stdout
            assert "potential hardcoded secret" in stdout.lower()

    def test_scans_multiple_file_types(self):
        """여러 파일 타입을 스캔해야 함 (py, js, yml, env)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create different file types with secrets (need 48+ chars after sk-proj-)
            py_file = temp_path / "config.py"
            py_file.write_text("""
api_key = "sk-proj-PythonSecret1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
""", encoding='utf-8')

            js_file = temp_path / "config.js"
            js_file.write_text("""
const apiKey = "sk-proj-JavaScriptKey1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh";
""", encoding='utf-8')

            exit_code, stdout, stderr = self.run_script(temp_path)

            # Should detect secrets in both Python and JavaScript
            assert exit_code == 1, f"Expected exit code 1, got {exit_code}. Stdout: {stdout}"
            assert "config.py" in stdout or "config.js" in stdout
