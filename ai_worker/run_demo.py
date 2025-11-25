#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Worker Demo Script - 전체 AI 파이프라인 시연

L(AI Worker)의 독립 실행을 시연하는 스크립트

Features:
    1. 파일 처리 (파싱 → 임베딩 → 저장)
    2. Article 840 태깅
    3. 벡터 검색
    4. 케이스 요약

Requirements:
    - OPENAI_API_KEY 환경변수 설정 필요
    - tests/fixtures/ 디렉토리에 테스트 파일 필요

Usage:
    python run_demo.py              # OpenAI API 필요 (전체 기능)
    python run_demo.py --offline    # API 없이 태깅만 테스트
"""

import sys
import os
import io
from pathlib import Path
from datetime import datetime

# Windows UTF-8 출력 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def print_header(title: str, emoji: str = "🚀"):
    """섹션 헤더 출력"""
    print(f"\n{'='*70}")
    print(f"{emoji} {title}")
    print(f"{'='*70}\n")


def print_success(msg: str):
    """성공 메시지 출력"""
    print(f"  ✅ {msg}")


def print_info(msg: str):
    """정보 메시지 출력"""
    print(f"  ℹ️  {msg}")


def print_error(msg: str):
    """에러 메시지 출력"""
    print(f"  ❌ {msg}")


def print_warning(msg: str):
    """경고 메시지 출력"""
    print(f"  ⚠️  {msg}")


def demo_article840_tagging():
    """
    데모 1: Article 840 태깅

    API 없이 로컬에서 실행 가능
    """
    print_header("Article 840 자동 태깅", "🏷️")

    try:
        from src.analysis.article_840_tagger import Article840Tagger
        from src.parsers.kakaotalk import KakaoTalkParser
        from src.parsers.text import TextParser

        # 테스트 파일 경로
        fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
        kakao_file = fixtures_dir / "kakaotalk_sample.txt"
        text_file = fixtures_dir / "text_sample.txt"

        # 1. 카카오톡 파일 태깅
        print("1️⃣ 카카오톡 대화 분석")
        if kakao_file.exists():
            parser = KakaoTalkParser()
            messages = parser.parse(str(kakao_file))
            print_info(f"파싱된 메시지: {len(messages)}개")

            tagger = Article840Tagger()
            results = tagger.tag_batch(messages)

            # 결과 집계
            category_counts = {}
            for result in results:
                for cat in result.categories:
                    category_counts[cat.value] = category_counts.get(cat.value, 0) + 1

            print_info("태깅 결과:")
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"     - {cat}: {count}건")

            print_success("카카오톡 태깅 완료")
        else:
            print_warning(f"테스트 파일 없음: {kakao_file}")

        # 2. 텍스트 파일 태깅
        print("\n2️⃣ 증거 문서 분석")
        if text_file.exists():
            parser = TextParser()
            messages = parser.parse(str(text_file))
            print_info(f"파싱된 메시지: {len(messages)}개")

            results = tagger.tag_batch(messages)

            # 결과 집계
            category_counts = {}
            for result in results:
                for cat in result.categories:
                    category_counts[cat.value] = category_counts.get(cat.value, 0) + 1

            print_info("태깅 결과:")
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"     - {cat}: {count}건")

            # 상세 결과 출력
            print("\n   📋 상세 분석 (처음 3개):")
            for i, (msg, result) in enumerate(zip(messages[:3], results[:3]), 1):
                content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                print(f"      [{i}] '{content_preview}'")
                print(f"          → {', '.join(c.value for c in result.categories)} (신뢰도: {result.confidence:.2f})")
                if result.matched_keywords:
                    print(f"          → 키워드: {', '.join(result.matched_keywords[:3])}")

            print_success("증거 문서 태깅 완료")
        else:
            print_warning(f"테스트 파일 없음: {text_file}")

        return True

    except Exception as e:
        print_error(f"태깅 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_file_processing():
    """
    데모 2: 파일 처리 (임베딩 생성 및 저장)

    OpenAI API 필요
    """
    print_header("파일 처리 (임베딩 → 저장)", "📁")

    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print_warning("OPENAI_API_KEY가 설정되지 않았습니다.")
        print_info("이 데모는 OpenAI API가 필요합니다.")
        print_info("설정: export OPENAI_API_KEY=your-api-key")
        return False

    try:
        from src.storage.storage_manager import StorageManager

        # 로컬 저장소 설정
        demo_db_path = Path(__file__).parent / "demo_data"
        demo_db_path.mkdir(parents=True, exist_ok=True)

        storage = StorageManager(
            vector_db_path=str(demo_db_path / "chromadb"),
            metadata_db_path=str(demo_db_path / "metadata.db")
        )

        # 테스트 파일 처리
        fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
        kakao_file = fixtures_dir / "kakaotalk_sample.txt"

        demo_case_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"   케이스 ID: {demo_case_id}")

        if kakao_file.exists():
            print_info(f"처리 파일: {kakao_file.name}")
            print_info("임베딩 생성 중... (OpenAI API 호출)")

            result = storage.process_file(
                filepath=str(kakao_file),
                case_id=demo_case_id
            )

            print_success(f"파일 처리 완료!")
            print(f"     - 파일 ID: {result['file_id']}")
            print(f"     - 총 메시지: {result['total_messages']}개")
            print(f"     - 저장된 청크: {result['chunks_stored']}개")

            return demo_case_id, storage
        else:
            print_warning(f"테스트 파일 없음: {kakao_file}")
            return None, None

    except Exception as e:
        print_error(f"파일 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def demo_search(case_id: str, storage):
    """
    데모 3: 벡터 검색

    OpenAI API 필요
    """
    print_header("벡터 검색", "🔍")

    if not case_id or not storage:
        print_warning("파일 처리가 먼저 필요합니다.")
        return False

    try:
        test_queries = [
            "이혼 소송",
            "증거 자료",
            "상담 예약"
        ]

        for query in test_queries:
            print(f"\n   검색어: '{query}'")
            print_info("임베딩 생성 및 검색 중...")

            results = storage.search(
                query=query,
                case_id=case_id,
                top_k=3
            )

            if results:
                print_success(f"{len(results)}개 결과 발견")
                for i, result in enumerate(results, 1):
                    content_preview = result['content'][:80] + "..." if len(result['content']) > 80 else result['content']
                    print(f"     [{i}] {content_preview}")
                    print(f"         거리: {result['distance']:.4f}")
            else:
                print_info("검색 결과 없음")

        return True

    except Exception as e:
        print_error(f"검색 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_case_summary(case_id: str, storage):
    """
    데모 4: 케이스 요약
    """
    print_header("케이스 요약", "📊")

    if not case_id or not storage:
        print_warning("파일 처리가 먼저 필요합니다.")
        return False

    try:
        # 케이스 요약 조회
        summary = storage.get_case_summary(case_id)

        print(f"   케이스 ID: {case_id}")
        print(f"   총 파일 수: {summary.get('total_files', 0)}개")
        print(f"   총 청크 수: {summary.get('total_chunks', 0)}개")

        # 파일 목록
        files = storage.get_case_files(case_id)
        if files:
            print("\n   📂 파일 목록:")
            for f in files:
                print(f"     - {f.filename} ({f.file_type}, {f.total_messages}개 메시지)")

        # 청크 샘플
        chunks = storage.get_case_chunks(case_id)
        if chunks:
            print(f"\n   📝 청크 샘플 (처음 5개):")
            for chunk in chunks[:5]:
                content_preview = chunk.content[:50] + "..." if len(chunk.content) > 50 else chunk.content
                sender = chunk.sender or "Unknown"
                print(f"     - [{sender}] {content_preview}")

        print_success("케이스 요약 완료")
        return True

    except Exception as e:
        print_error(f"케이스 요약 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_offline():
    """
    오프라인 데모 (API 불필요)
    """
    print_header("AI Worker 오프라인 데모", "🖥️")
    print_info("OpenAI API 없이 실행 가능한 기능을 테스트합니다.\n")

    # 1. Article 840 태깅 (API 불필요)
    demo_article840_tagging()

    print_header("데모 완료", "🎉")
    print_info("오프라인 데모 완료")
    print_info("전체 기능 테스트: python run_demo.py (OPENAI_API_KEY 필요)")


def demo_full():
    """
    전체 데모 (API 필요)
    """
    print_header("AI Worker 전체 데모", "🚀")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"   시작 시간: {timestamp}")

    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print_warning("\nOPENAI_API_KEY가 설정되지 않았습니다.")
        print_info("오프라인 모드로 전환합니다...\n")
        demo_offline()
        return

    print_info("OpenAI API 키 확인됨 ✓\n")

    # 1. Article 840 태깅
    demo_article840_tagging()

    # 2. 파일 처리
    case_id, storage = demo_file_processing()

    if case_id and storage:
        # 3. 검색
        demo_search(case_id, storage)

        # 4. 케이스 요약
        demo_case_summary(case_id, storage)

    print_header("데모 완료", "🎉")
    print_info("AI Worker 전체 파이프라인 시연 완료!")

    if case_id:
        print(f"\n   생성된 데이터:")
        print(f"   - 케이스 ID: {case_id}")
        print(f"   - 데이터 위치: {Path(__file__).parent / 'demo_data'}")

    print("\n   CLI 도구 사용법:")
    print("   python cli.py process --file <파일> --case-id <케이스ID>")
    print("   python cli.py search --query <검색어> --case-id <케이스ID>")
    print("   python cli.py summary --case-id <케이스ID>")
    print("   python cli.py analyze --file <파일>")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Worker 데모 스크립트"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="오프라인 모드 (API 없이 태깅만 테스트)"
    )
    parser.add_argument(
        "--tagging-only",
        action="store_true",
        help="Article 840 태깅만 실행"
    )

    args = parser.parse_args()

    if args.tagging_only:
        print_header("Article 840 태깅 데모", "🏷️")
        demo_article840_tagging()
    elif args.offline:
        demo_offline()
    else:
        demo_full()


if __name__ == "__main__":
    main()
