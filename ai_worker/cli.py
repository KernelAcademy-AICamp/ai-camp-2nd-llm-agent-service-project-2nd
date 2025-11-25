#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Worker CLI - 독립 실행 도구

L(AI Worker)를 백엔드 없이 독립적으로 실행하기 위한 CLI 도구

Usage:
    python cli.py process --file <filepath> --case-id <case_id>
    python cli.py search --query <query> --case-id <case_id>
    python cli.py summary --case-id <case_id>
    python cli.py list [--case-id <case_id>]
    python cli.py analyze --file <filepath>
"""

import argparse
import sys
import os
import io
import json
from pathlib import Path
from typing import Optional

# Windows UTF-8 출력 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# .env 파일 로드
from dotenv import load_dotenv
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

from src.storage.storage_manager import StorageManager
from src.analysis.article_840_tagger import Article840Tagger, TaggingResult
from src.parsers.kakaotalk import KakaoTalkParser
from src.parsers.text import TextParser
from src.parsers.base import Message


def get_storage_manager(data_dir: str = "./local_db") -> StorageManager:
    """
    StorageManager 인스턴스 생성 (로컬 저장소 사용)

    Args:
        data_dir: 데이터 저장 디렉토리

    Returns:
        StorageManager: 로컬 스토리지 매니저
    """
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    return StorageManager(
        vector_db_path=str(data_path / "chromadb"),
        metadata_db_path=str(data_path / "metadata.db")
    )


def cmd_process(args):
    """
    파일 처리 커맨드

    Given: 파일 경로와 케이스 ID
    When: 파일을 파싱하고 임베딩 생성 후 저장
    Then: 처리 결과 출력
    """
    print(f"\n{'='*60}")
    print(f"📁 파일 처리: {args.file}")
    print(f"📋 케이스 ID: {args.case_id}")
    print(f"{'='*60}\n")

    # 파일 존재 확인
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"❌ 오류: 파일을 찾을 수 없습니다 - {filepath}")
        return 1

    try:
        storage = get_storage_manager(args.data_dir)

        print("🔄 파일 처리 중...")
        result = storage.process_file(
            filepath=str(filepath.absolute()),
            case_id=args.case_id
        )

        print(f"\n✅ 처리 완료!")
        print(f"   - 파일 ID: {result['file_id']}")
        print(f"   - 총 메시지: {result['total_messages']}개")
        print(f"   - 저장된 청크: {result['chunks_stored']}개")

        # Article 840 태깅 (선택적)
        if args.tag:
            print(f"\n🏷️ Article 840 태깅 수행 중...")
            _perform_tagging(filepath, args.case_id)

        return 0

    except Exception as e:
        print(f"\n❌ 처리 실패: {e}")
        return 1


def cmd_search(args):
    """
    검색 커맨드

    Given: 검색 쿼리와 케이스 ID
    When: 벡터 검색 수행
    Then: 검색 결과 출력
    """
    print(f"\n{'='*60}")
    print(f"🔍 검색: '{args.query}'")
    print(f"📋 케이스 ID: {args.case_id}")
    print(f"{'='*60}\n")

    try:
        storage = get_storage_manager(args.data_dir)

        print("🔄 검색 중...")
        results = storage.search(
            query=args.query,
            case_id=args.case_id,
            top_k=args.top_k
        )

        if not results:
            print("📭 검색 결과가 없습니다.")
            return 0

        print(f"\n✅ {len(results)}개 결과 발견:\n")

        for i, result in enumerate(results, 1):
            print(f"--- 결과 {i} ---")
            print(f"📄 내용: {result['content'][:200]}...")
            print(f"📊 거리: {result['distance']:.4f}")
            if result.get('metadata'):
                meta = result['metadata']
                print(f"👤 발신자: {meta.get('sender', 'N/A')}")
                print(f"📁 파일 ID: {meta.get('file_id', 'N/A')}")
            print()

        return 0

    except Exception as e:
        print(f"\n❌ 검색 실패: {e}")
        return 1


def cmd_summary(args):
    """
    케이스 요약 커맨드

    Given: 케이스 ID
    When: 케이스 요약 정보 조회
    Then: 요약 출력
    """
    print(f"\n{'='*60}")
    print(f"📊 케이스 요약: {args.case_id}")
    print(f"{'='*60}\n")

    try:
        storage = get_storage_manager(args.data_dir)

        # 케이스 요약 조회
        summary = storage.get_case_summary(args.case_id)

        if not summary or summary.get('total_files', 0) == 0:
            print(f"📭 케이스 '{args.case_id}'에 대한 데이터가 없습니다.")
            return 0

        print(f"📁 총 파일 수: {summary.get('total_files', 0)}개")
        print(f"📝 총 청크 수: {summary.get('total_chunks', 0)}개")

        # 파일 목록 조회
        files = storage.get_case_files(args.case_id)
        if files:
            print(f"\n📂 파일 목록:")
            for f in files:
                print(f"   - {f.filename} ({f.file_type}, {f.total_messages}개 메시지)")

        # LLM 요약 (선택적)
        if args.llm:
            print(f"\n🤖 LLM 요약 생성 중...")
            _generate_llm_summary(storage, args.case_id)

        return 0

    except Exception as e:
        print(f"\n❌ 요약 실패: {e}")
        return 1


def cmd_list(args):
    """
    목록 조회 커맨드

    Given: 케이스 ID (선택적)
    When: 데이터 목록 조회
    Then: 파일/케이스 목록 출력
    """
    print(f"\n{'='*60}")
    print(f"📋 데이터 목록")
    print(f"{'='*60}\n")

    try:
        storage = get_storage_manager(args.data_dir)

        if args.case_id:
            # 특정 케이스의 파일 목록
            files = storage.get_case_files(args.case_id)

            if not files:
                print(f"📭 케이스 '{args.case_id}'에 대한 파일이 없습니다.")
                return 0

            print(f"케이스 '{args.case_id}' 파일 목록:\n")
            for f in files:
                print(f"📄 {f.filename}")
                print(f"   - ID: {f.file_id}")
                print(f"   - 타입: {f.file_type}")
                print(f"   - 메시지: {f.total_messages}개")
                print(f"   - 경로: {f.filepath}")
                print()

            # 청크 목록도 출력 (선택적)
            if args.verbose:
                chunks = storage.get_case_chunks(args.case_id)
                print(f"\n📝 청크 목록 ({len(chunks)}개):\n")
                for chunk in chunks[:10]:  # 처음 10개만
                    content_preview = chunk.content[:50] + "..." if len(chunk.content) > 50 else chunk.content
                    print(f"   - [{chunk.sender}] {content_preview}")

                if len(chunks) > 10:
                    print(f"   ... 외 {len(chunks) - 10}개")
        else:
            # 모든 케이스 목록 (메타데이터 스토어에서 조회)
            print("💡 특정 케이스를 조회하려면 --case-id 옵션을 사용하세요.")
            print("   예: python cli.py list --case-id case001")

        return 0

    except Exception as e:
        print(f"\n❌ 목록 조회 실패: {e}")
        return 1


def cmd_analyze(args):
    """
    Article 840 분석 커맨드

    Given: 파일 경로
    When: 파일을 파싱하고 Article 840 태깅 수행
    Then: 분석 결과 출력
    """
    print(f"\n{'='*60}")
    print(f"🏷️ Article 840 분석: {args.file}")
    print(f"{'='*60}\n")

    # 파일 존재 확인
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"❌ 오류: 파일을 찾을 수 없습니다 - {filepath}")
        return 1

    try:
        # 파일 파싱
        print("🔄 파일 파싱 중...")
        messages = _parse_file(filepath)

        if not messages:
            print("📭 파싱된 메시지가 없습니다.")
            return 0

        print(f"   {len(messages)}개 메시지 파싱 완료\n")

        # Article 840 태깅
        print("🏷️ Article 840 태깅 중...")
        tagger = Article840Tagger()
        results = tagger.tag_batch(messages)

        # 카테고리별 집계
        category_counts = {}
        for result in results:
            for category in result.categories:
                cat_name = category.value
                category_counts[cat_name] = category_counts.get(cat_name, 0) + 1

        print(f"\n✅ 태깅 결과 요약:\n")

        # 카테고리별 출력
        category_names = {
            "adultery": "부정행위 (제1호)",
            "desertion": "악의의 유기 (제2호)",
            "mistreatment_by_inlaws": "시가 부당대우 (제3호)",
            "harm_to_own_parents": "친가 학대 (제4호)",
            "unknown_whereabouts": "생사불명 (제5호)",
            "irreconcilable_differences": "혼인 지속 곤란 (제6호)",
            "general": "일반 증거"
        }

        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            cat_display = category_names.get(cat, cat)
            print(f"   📌 {cat_display}: {count}건")

        # 상세 결과 (선택적)
        if args.verbose:
            print(f"\n📋 상세 결과:\n")
            for i, (msg, result) in enumerate(zip(messages[:10], results[:10]), 1):
                print(f"--- 메시지 {i} ---")
                print(f"👤 발신자: {msg.sender}")
                print(f"📄 내용: {msg.content[:100]}...")
                print(f"🏷️ 카테고리: {', '.join(c.value for c in result.categories)}")
                print(f"📊 신뢰도: {result.confidence:.2f}")
                print(f"💡 이유: {result.reasoning}")
                print()

            if len(messages) > 10:
                print(f"... 외 {len(messages) - 10}개 메시지")

        return 0

    except Exception as e:
        print(f"\n❌ 분석 실패: {e}")
        return 1


def _parse_file(filepath: Path) -> list:
    """
    파일 타입에 따라 적절한 파서로 파싱

    Args:
        filepath: 파일 경로

    Returns:
        list: Message 객체 리스트
    """
    # 파일 타입 감지
    if "kakao" in filepath.name.lower():
        parser = KakaoTalkParser()
    else:
        parser = TextParser()

    return parser.parse(str(filepath))


def _perform_tagging(filepath: Path, case_id: str):
    """
    파일에 대해 Article 840 태깅 수행

    Args:
        filepath: 파일 경로
        case_id: 케이스 ID
    """
    messages = _parse_file(filepath)
    tagger = Article840Tagger()
    results = tagger.tag_batch(messages)

    # 카테고리별 집계
    category_counts = {}
    for result in results:
        for category in result.categories:
            cat_name = category.value
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1

    print(f"\n   태깅 결과:")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {cat}: {count}건")


def _generate_llm_summary(storage: StorageManager, case_id: str):
    """
    LLM을 사용한 케이스 요약 생성

    Args:
        storage: StorageManager 인스턴스
        case_id: 케이스 ID
    """
    try:
        from src.analysis.summarizer import EvidenceSummarizer

        # 청크 조회
        chunks = storage.get_case_chunks(case_id)

        if not chunks:
            print("   요약할 데이터가 없습니다.")
            return

        # Message 객체로 변환
        messages = [
            Message(
                content=chunk.content,
                sender=chunk.sender or "Unknown",
                timestamp=chunk.timestamp
            )
            for chunk in chunks[:50]  # 처음 50개만 요약
        ]

        # 요약 생성
        summarizer = EvidenceSummarizer()
        result = summarizer.summarize_evidence(messages)

        print(f"\n   📝 요약:")
        print(f"   {result.summary}")

        if result.key_points:
            print(f"\n   🔑 핵심 포인트:")
            for point in result.key_points:
                print(f"   - {point}")

    except Exception as e:
        print(f"   ⚠️ LLM 요약 생성 실패: {e}")


def main():
    """
    메인 함수 - CLI 인터페이스 정의
    """
    parser = argparse.ArgumentParser(
        description="AI Worker CLI - 독립 실행 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
    # 파일 처리 (임베딩 생성 및 저장)
    python cli.py process --file ./test_data/kakaotalk.txt --case-id case001

    # 검색
    python cli.py search --query "폭력" --case-id case001

    # 케이스 요약
    python cli.py summary --case-id case001

    # 파일 목록
    python cli.py list --case-id case001

    # Article 840 분석
    python cli.py analyze --file ./test_data/kakaotalk.txt
        """
    )

    # 공통 옵션
    parser.add_argument(
        "--data-dir",
        default="./local_db",
        help="로컬 데이터 저장 디렉토리 (기본: ./local_db)"
    )

    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 커맨드")

    # process 커맨드
    process_parser = subparsers.add_parser("process", help="파일 처리 (파싱 → 임베딩 → 저장)")
    process_parser.add_argument("--file", "-f", required=True, help="처리할 파일 경로")
    process_parser.add_argument("--case-id", "-c", required=True, help="케이스 ID")
    process_parser.add_argument("--tag", "-t", action="store_true", help="Article 840 태깅 수행")
    process_parser.set_defaults(func=cmd_process)

    # search 커맨드
    search_parser = subparsers.add_parser("search", help="증거 검색")
    search_parser.add_argument("--query", "-q", required=True, help="검색 쿼리")
    search_parser.add_argument("--case-id", "-c", required=True, help="케이스 ID")
    search_parser.add_argument("--top-k", "-k", type=int, default=10, help="검색 결과 수 (기본: 10)")
    search_parser.set_defaults(func=cmd_search)

    # summary 커맨드
    summary_parser = subparsers.add_parser("summary", help="케이스 요약")
    summary_parser.add_argument("--case-id", "-c", required=True, help="케이스 ID")
    summary_parser.add_argument("--llm", "-l", action="store_true", help="LLM 기반 요약 생성")
    summary_parser.set_defaults(func=cmd_summary)

    # list 커맨드
    list_parser = subparsers.add_parser("list", help="데이터 목록 조회")
    list_parser.add_argument("--case-id", "-c", help="케이스 ID (선택적)")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="상세 정보 출력")
    list_parser.set_defaults(func=cmd_list)

    # analyze 커맨드
    analyze_parser = subparsers.add_parser("analyze", help="Article 840 분석")
    analyze_parser.add_argument("--file", "-f", required=True, help="분석할 파일 경로")
    analyze_parser.add_argument("--verbose", "-v", action="store_true", help="상세 결과 출력")
    analyze_parser.set_defaults(func=cmd_analyze)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # OpenAI API 키 확인 (process, search, summary 시 필요)
    if args.command in ["process", "search"] and not os.getenv("OPENAI_API_KEY"):
        print("⚠️ 주의: OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   임베딩 생성에 OpenAI API가 필요합니다.")
        print("   설정: export OPENAI_API_KEY=your-api-key")
        print()

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
