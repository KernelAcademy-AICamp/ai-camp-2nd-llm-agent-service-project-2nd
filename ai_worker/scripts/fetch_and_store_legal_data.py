"""
법률 데이터 수집 및 Qdrant 저장 스크립트

국가법령정보 API에서 이혼 관련 법률 데이터를 수집하고
Qdrant Cloud에 저장합니다.

사용법:
    python scripts/fetch_and_store_legal_data.py <회원ID>

환경변수:
    LAW_API_MEMBER_ID: 국가법령정보 공동활용 회원 ID
    QDRANT_HOST: Qdrant Cloud URL
    QDRANT_API_KEY: Qdrant API Key
    OPENAI_API_KEY: OpenAI API Key (임베딩용)
"""

import os
import sys
from pathlib import Path
from datetime import date
import logging

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# 환경변수 로드
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

from src.service_rag.legal_api_fetcher import LegalAPIClient, StatuteArticle, PrecedentData
from src.service_rag.schemas import Statute, CaseLaw
from src.service_rag.legal_vectorizer import LegalVectorizer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_article_to_statute(article: StatuteArticle) -> Statute:
    """StatuteArticle을 Statute 모델로 변환"""
    return Statute(
        statute_id=f"civil_law_{article.article_number.replace('제', '').replace('조', '')}",
        name=article.law_name,
        article_number=article.article_number,
        content=f"{article.article_title}\n\n{article.content}".strip(),
        effective_date=None,  # API에서 파싱 필요
        category="민법_이혼"
    )


def convert_precedent_to_caselaw(precedent: PrecedentData) -> CaseLaw:
    """PrecedentData를 CaseLaw 모델로 변환"""
    # 판결일 파싱 (YYYYMMDD 형식)
    decision_date = date.today()
    if precedent.judgment_date:
        try:
            year = int(precedent.judgment_date[:4])
            month = int(precedent.judgment_date[4:6])
            day = int(precedent.judgment_date[6:8])
            decision_date = date(year, month, day)
        except (ValueError, IndexError):
            pass

    return CaseLaw(
        case_id=precedent.precedent_id or f"prec_{precedent.case_number}",
        case_number=precedent.case_number,
        court=precedent.court_name,
        decision_date=decision_date,
        case_name=f"{precedent.case_type} - {precedent.case_number}",
        summary=precedent.summary,
        full_text=precedent.full_text,
        category="이혼_가사"
    )


def fetch_and_store_statutes(client: LegalAPIClient, vectorizer: LegalVectorizer) -> int:
    """
    이혼 관련 법령 조문 수집 및 저장

    Returns:
        저장된 조문 수
    """
    logger.info("=== 이혼 관련 법령 조문 수집 시작 ===")

    # 이혼 관련 조문 가져오기
    articles = client.get_civil_law_divorce_articles()

    if not articles:
        logger.warning("API에서 조문을 가져오지 못했습니다.")
        return 0

    logger.info(f"총 {len(articles)}개 조문 수집됨")

    # Statute 모델로 변환 및 저장
    success_count = 0
    for article in articles:
        try:
            statute = convert_article_to_statute(article)
            chunk_id = vectorizer.vectorize_statute(statute)
            logger.info(f"저장 완료: {article.article_number} -> {chunk_id}")
            success_count += 1
        except Exception as e:
            logger.error(f"저장 실패 ({article.article_number}): {e}")

    return success_count


def fetch_and_store_precedents(client: LegalAPIClient, vectorizer: LegalVectorizer, max_count: int = 30) -> int:
    """
    이혼 관련 판례 수집 및 저장

    Args:
        max_count: 최대 수집 개수

    Returns:
        저장된 판례 수
    """
    logger.info("=== 이혼 관련 판례 수집 시작 ===")

    # 이혼 관련 판례 가져오기
    precedents = client.get_divorce_precedents(max_count=max_count)

    if not precedents:
        logger.warning("API에서 판례를 가져오지 못했습니다.")
        return 0

    logger.info(f"총 {len(precedents)}개 판례 수집됨")

    # CaseLaw 모델로 변환 및 저장
    success_count = 0
    for precedent in precedents:
        try:
            if not precedent.summary:
                logger.warning(f"요지 없음, 건너뜀: {precedent.case_number}")
                continue

            case_law = convert_precedent_to_caselaw(precedent)
            chunk_id = vectorizer.vectorize_case_law(case_law)
            logger.info(f"저장 완료: {precedent.case_number} -> {chunk_id}")
            success_count += 1
        except Exception as e:
            logger.error(f"저장 실패 ({precedent.case_number}): {e}")

    return success_count


def main():
    """메인 실행"""
    # 회원 ID 확인
    member_id = os.getenv("LAW_API_MEMBER_ID")
    if not member_id and len(sys.argv) > 1:
        member_id = sys.argv[1]

    if not member_id:
        print("=" * 60)
        print("국가법령정보 공동활용 회원 ID가 필요합니다.")
        print()
        print("설정 방법:")
        print("  1. 환경변수: export LAW_API_MEMBER_ID=<회원ID>")
        print("  2. 인자: python fetch_and_store_legal_data.py <회원ID>")
        print()
        print("회원 ID 확인:")
        print("  - open.law.go.kr 로그인 후 마이페이지에서 확인")
        print("  - API 요청 시 OC 파라미터 값으로 사용됩니다")
        print("=" * 60)
        sys.exit(1)

    # 필수 환경변수 확인
    required_env = ["QDRANT_HOST", "QDRANT_API_KEY", "OPENAI_API_KEY"]
    missing = [env for env in required_env if not os.getenv(env)]

    if missing:
        print("=" * 60)
        print("다음 환경변수가 설정되지 않았습니다:")
        for env in missing:
            print(f"  - {env}")
        print()
        print("ai_worker/.env 파일을 확인하세요.")
        print("=" * 60)
        sys.exit(1)

    print("=" * 60)
    print("법률 데이터 수집 및 저장 시작")
    print(f"회원 ID: {member_id[:4]}***")
    print(f"Qdrant: {os.getenv('QDRANT_HOST')[:30]}...")
    print("=" * 60)

    # 클라이언트 초기화
    api_client = LegalAPIClient(member_id=member_id)
    vectorizer = LegalVectorizer(collection_name="leh_legal_knowledge")

    # 법령 수집 및 저장
    statute_count = fetch_and_store_statutes(api_client, vectorizer)

    # 판례 수집 및 저장
    precedent_count = fetch_and_store_precedents(api_client, vectorizer, max_count=30)

    # 결과 출력
    print()
    print("=" * 60)
    print("수집 및 저장 완료")
    print(f"  - 법령 조문: {statute_count}개")
    print(f"  - 판례: {precedent_count}개")
    print(f"  - 총: {statute_count + precedent_count}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
