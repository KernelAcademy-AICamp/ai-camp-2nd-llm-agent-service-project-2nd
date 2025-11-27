"""
Pytest Configuration - 테스트 환경 설정

환경변수 로드 및 공통 fixtures 정의
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """
    pytest 설정 시 환경변수 로드

    .env 파일 위치:
    1. leh-ai-pipeline/.env (우선)
    2. ai-camp-2nd-llm-agent-service-project-2nd/ai_worker/.env (fallback)
    """
    try:
        from dotenv import load_dotenv

        # 가능한 .env 파일 경로들
        env_paths = [
            project_root / ".env",
            project_root.parent / "ai-camp-2nd-llm-agent-service-project-2nd" / "ai_worker" / ".env",
            project_root.parent / "ai_worker" / ".env",
        ]

        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                print(f"\n[conftest] Loaded environment from: {env_path}")
                break
        else:
            print("\n[conftest] Warning: No .env file found")

    except ImportError:
        print("\n[conftest] Warning: python-dotenv not installed, skipping .env load")


def pytest_collection_modifyitems(config, items):
    """
    테스트 수집 후 Real API 테스트 상태 출력
    """
    real_tests = [item for item in items if "real" in item.keywords]
    if real_tests:
        has_key = bool(os.getenv("OPENAI_API_KEY"))
        status = "ENABLED" if has_key else "SKIPPED (no API key)"
        print(f"\n[conftest] Real API tests: {len(real_tests)} tests - {status}")
