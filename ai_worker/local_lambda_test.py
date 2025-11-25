"""
Local Lambda Test Runner
SAM CLI 없이 Lambda 핸들러를 로컬에서 테스트합니다.

Usage:
    python local_lambda_test.py                    # 기본 테스트 (카카오톡 파일)
    python local_lambda_test.py --event events/s3_kakaotalk_event.json
    python local_lambda_test.py --file tests/fixtures/kakaotalk_sample.txt
"""

import json
import os
import sys
import shutil
import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))


def create_mock_s3_event(bucket: str, key: str) -> dict:
    """S3 이벤트 생성"""
    return {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "ap-northeast-2",
                "eventTime": datetime.now().isoformat(),
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {
                        "name": bucket,
                        "arn": f"arn:aws:s3:::{bucket}"
                    },
                    "object": {
                        "key": key,
                        "size": 1024
                    }
                }
            }
        ]
    }


def setup_test_environment():
    """테스트 환경 설정"""
    os.environ.setdefault("ENVIRONMENT", "local")
    os.environ.setdefault("AWS_REGION", "ap-northeast-2")
    os.environ.setdefault("OPENAI_API_KEY", "test-key-for-local")

    # /tmp 디렉토리 생성 (Windows 호환)
    tmp_dir = Path("/tmp") if os.name != "nt" else Path("./tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    return tmp_dir


def mock_s3_download(local_file: str):
    """S3 다운로드를 로컬 파일 복사로 대체"""
    def download_side_effect(bucket, key, local_path):
        print(f"  [Mock S3] Copying {local_file} -> {local_path}")
        shutil.copy(local_file, local_path)
    return download_side_effect


def mock_openai_embedding():
    """OpenAI 임베딩 Mock"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1] * 768)]
    mock_client.embeddings.create.return_value = mock_response
    return mock_client


def run_local_test(
    event_file: str = None,
    local_file: str = None,
    bucket: str = "leh-evidence-dev",
    key: str = "cases/test/sample.txt"
):
    """로컬 Lambda 테스트 실행"""
    print("=" * 60)
    print("LEH AI Worker - Local Lambda Test")
    print("=" * 60)

    # 1. 환경 설정
    tmp_dir = setup_test_environment()
    print(f"\n[1] Environment: {os.getenv('ENVIRONMENT')}")
    print(f"    Temp dir: {tmp_dir}")

    # 2. 이벤트 로드 또는 생성
    if event_file:
        print(f"\n[2] Loading event from: {event_file}")
        with open(event_file) as f:
            event = json.load(f)
        # 이벤트에서 bucket/key 추출
        s3_info = event["Records"][0]["s3"]
        bucket = s3_info["bucket"]["name"]
        key = s3_info["object"]["key"]
    else:
        print(f"\n[2] Creating S3 event: s3://{bucket}/{key}")
        event = create_mock_s3_event(bucket, key)

    # 3. 테스트 파일 결정
    if not local_file:
        # 기본 fixture 파일 사용
        fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
        if "kakaotalk" in key.lower():
            local_file = str(fixtures_dir / "kakaotalk_sample.txt")
        elif key.endswith(".txt"):
            local_file = str(fixtures_dir / "text_sample.txt")
        else:
            local_file = str(fixtures_dir / "kakaotalk_sample.txt")

    print(f"\n[3] Using local file: {local_file}")

    if not Path(local_file).exists():
        print(f"    ERROR: File not found: {local_file}")
        return None

    # 4. Mock 설정 및 핸들러 실행
    print("\n[4] Running Lambda handler with mocks...")
    print("    - Mock: S3 download")
    print("    - Mock: OpenAI embeddings")
    print("    - Mock: Article840Tagger")

    with patch('boto3.client') as mock_boto3, \
         patch('openai.OpenAI') as mock_openai, \
         patch('handler.Article840Tagger') as mock_tagger:

        # S3 Mock
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.download_file.side_effect = mock_s3_download(local_file)

        # OpenAI Mock
        mock_openai.return_value = mock_openai_embedding()

        # Article840Tagger Mock
        mock_tagger_instance = MagicMock()
        mock_tagger_instance.tag.return_value = MagicMock(
            categories=[],
            confidence=0.0,
            matched_keywords=[]
        )
        mock_tagger.return_value = mock_tagger_instance

        # Import and run handler
        from handler import handle

        context = MagicMock()
        context.function_name = "leh-ai-worker-local"
        context.memory_limit_in_mb = 1024
        context.invoked_function_arn = "arn:aws:lambda:local:000000000000:function:test"

        result = handle(event, context)

    # 5. 결과 출력
    print("\n[5] Result:")
    print("-" * 40)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 6. 검증
    print("\n[6] Validation:")
    body = json.loads(result.get("body", "{}"))
    results = body.get("results", [])

    if results:
        for r in results:
            status = r.get("status")
            if status == "processed":
                print(f"    OK: File processed successfully")
                print(f"        - file_id: {r.get('file_id', 'N/A')}")
                print(f"        - chunks_indexed: {r.get('chunks_indexed', 0)}")
                print(f"        - parser: {r.get('parser_type', 'N/A')}")
            elif status == "error":
                print(f"    ERROR: {r.get('error', 'Unknown error')}")
            else:
                print(f"    SKIPPED: {r.get('reason', 'Unknown')}")
    else:
        print("    WARNING: No results returned")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

    return result


def cleanup_test_data():
    """테스트 데이터 정리"""
    # Windows용 tmp 정리
    tmp_dir = Path("./tmp")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # /tmp 하위 테스트 데이터 정리
    for pattern in ["chromadb", "metadata.db"]:
        path = Path("/tmp") / pattern
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local Lambda Test Runner")
    parser.add_argument(
        "--event",
        help="Path to S3 event JSON file",
        default=None
    )
    parser.add_argument(
        "--file",
        help="Local file to process (instead of S3 download)",
        default=None
    )
    parser.add_argument(
        "--bucket",
        help="S3 bucket name",
        default="leh-evidence-dev"
    )
    parser.add_argument(
        "--key",
        help="S3 object key",
        default="cases/test/kakaotalk_sample.txt"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up test data after running"
    )

    args = parser.parse_args()

    try:
        result = run_local_test(
            event_file=args.event,
            local_file=args.file,
            bucket=args.bucket,
            key=args.key
        )
    finally:
        if args.cleanup:
            print("\nCleaning up test data...")
            cleanup_test_data()
