"""
Unit tests for app/core/config.py

TDD approach: Test configuration loading, validation, and computed properties
"""

import pytest
import os
from app.core.config import Settings


@pytest.mark.unit
class TestSettings:
    """Test Settings class configuration"""

    def test_settings_loads_from_env(self, test_env):
        """Test that Settings correctly loads from environment variables"""
        settings = Settings()

        assert settings.APP_ENV == "local"
        assert settings.APP_DEBUG is True
        assert settings.JWT_SECRET == "test-secret-key-do-not-use-in-production"
        assert settings.S3_EVIDENCE_BUCKET == "test-bucket"

    def test_settings_default_values(self):
        """Test that Settings has correct default values"""
        # Clear env vars temporarily
        original_env = os.environ.copy()
        for key in list(os.environ.keys()):
            if key.startswith(('APP_', 'JWT_', 'S3_', 'POSTGRES_', 'AWS_', 'OPENAI_')):
                os.environ.pop(key, None)

        try:
            settings = Settings()

            assert settings.APP_NAME == "legal-evidence-hub"
            assert settings.APP_ENV == "local"
            assert settings.APP_DEBUG is True
            assert settings.BACKEND_HOST == "0.0.0.0"
            assert settings.BACKEND_PORT == 8000
            assert settings.JWT_ALGORITHM == "HS256"
            assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 60

        finally:
            # Restore env vars
            os.environ.clear()
            os.environ.update(original_env)

    def test_cors_origins_list_property(self, test_env):
        """Test that cors_origins_list property correctly splits string"""
        settings = Settings(
            CORS_ALLOW_ORIGINS="http://localhost:3000,http://localhost:5173,https://example.com"
        )

        origins = settings.cors_origins_list

        assert isinstance(origins, list)
        assert len(origins) == 3
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins
        assert "https://example.com" in origins

    def test_cors_origins_list_strips_whitespace(self, test_env):
        """Test that cors_origins_list strips whitespace from origins"""
        settings = Settings(
            CORS_ALLOW_ORIGINS="http://localhost:3000 , http://localhost:5173 ,  https://example.com"
        )

        origins = settings.cors_origins_list

        assert "http://localhost:3000" in origins  # No trailing/leading spaces
        assert " http://localhost:5173 " not in origins

    def test_database_url_computed_property_uses_explicit_url(self, test_env):
        """Test that database_url_computed uses explicit DATABASE_URL if provided"""
        explicit_url = "postgresql://custom:password@custom-host:5432/custom_db"
        settings = Settings(DATABASE_URL=explicit_url)

        assert settings.database_url_computed == explicit_url

    def test_database_url_computed_property_constructs_from_parts(self, test_env):
        """Test that database_url_computed constructs URL from individual components"""
        settings = Settings(
            DATABASE_URL="",
            POSTGRES_HOST="testhost",
            POSTGRES_PORT=5432,
            POSTGRES_USER="testuser",
            POSTGRES_PASSWORD="testpass",
            POSTGRES_DB="testdb"
        )

        expected_url = "postgresql+psycopg2://testuser:testpass@testhost:5432/testdb"
        assert settings.database_url_computed == expected_url

    def test_s3_presigned_url_max_expire_seconds(self, test_env):
        """Test that S3 presigned URL expiry has a maximum limit (security requirement)"""
        settings = Settings()

        # Default should be 300 seconds (5 minutes) per SECURITY_COMPLIANCE.md
        assert settings.S3_PRESIGNED_URL_EXPIRE_SECONDS == 300

    def test_feature_flags_default_values(self, test_env):
        """Test that feature flags have correct default values"""
        settings = Settings()

        # Per PRD.md, these must be True in production
        assert settings.FEATURE_DRAFT_PREVIEW_ONLY is True
        assert settings.FEATURE_ENABLE_RAG_SEARCH is True
        assert settings.FEATURE_ENABLE_TIMELINE_VIEW is True

    def test_aws_region_default(self, test_env):
        """Test that AWS region defaults to ap-northeast-2 (Seoul)"""
        settings = Settings()

        assert settings.AWS_REGION == "ap-northeast-2"

    def test_openai_model_defaults(self, test_env):
        """Test that OpenAI model names have sensible defaults"""
        settings = Settings()

        assert settings.OPENAI_MODEL_CHAT == "gpt-4o-mini"
        assert settings.OPENAI_MODEL_EMBEDDING == "text-embedding-3-small"

    def test_log_level_default(self, test_env):
        """Test that log level defaults to INFO"""
        settings = Settings()

        assert settings.LOG_LEVEL == "INFO"

    def test_settings_validation_empty_jwt_secret_in_prod(self):
        """Test that JWT_SECRET should not be empty in production (future validation)"""
        # This test documents expected behavior for future validation
        # TODO: Add pydantic validator to enforce strong JWT_SECRET in prod

        settings = Settings(
            APP_ENV="prod",
            JWT_SECRET="weak"  # Should trigger validation error in future
        )

        # For now, just verify it loads (validation to be added)
        assert settings.JWT_SECRET == "weak"
        # Future: should raise ValidationError

    def test_opensearch_case_index_prefix(self, test_env):
        """Test that OpenSearch case index prefix is correct"""
        settings = Settings()

        assert settings.OPENSEARCH_CASE_INDEX_PREFIX == "case_rag_"

    def test_opensearch_default_top_k(self, test_env):
        """Test that OpenSearch default top-k is 5"""
        settings = Settings()

        assert settings.OPENSEARCH_DEFAULT_TOP_K == 5
