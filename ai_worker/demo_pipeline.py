"""
AI Worker V2 파이프라인 데모/테스트 스크립트

사용법:
    python demo_pipeline.py                     # 샘플 데이터로 테스트
    python demo_pipeline.py 카톡파일.txt        # 실제 파일로 테스트
    python demo_pipeline.py image.jpg           # 이미지 파일
    python demo_pipeline.py document.pdf        # PDF 파일
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.parsers.kakaotalk_v2 import KakaoTalkParserV2
from src.parsers.pdf_parser_v2 import PDFParserV2
from src.parsers.image_parser_v2 import ImageParserV2
from src.analysis.legal_analyzer import LegalAnalyzer


def print_header(title: str):
    """섹션 헤더 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_chunk(chunk, index: int):
    """청크 정보 출력"""
    loc = chunk.source_location
    analysis = chunk.legal_analysis

    # 위치 정보
    if loc.line_number:
        location_str = f"{loc.file_name} {loc.line_number}번째 줄"
    elif loc.page_number:
        location_str = f"{loc.file_name} {loc.page_number}페이지"
    elif loc.image_index:
        location_str = f"{loc.file_name} (이미지 #{loc.image_index})"
    else:
        location_str = loc.file_name

    print(f"\n[{index}] {location_str}")
    print(f"    발신자: {chunk.sender or 'N/A'}")
    print(f"    내용: {chunk.content[:80]}{'...' if len(chunk.content) > 80 else ''}")

    if analysis:
        categories = [c.value if hasattr(c, 'value') else c for c in analysis.categories]
        conf_name = analysis.confidence_level.name if hasattr(analysis.confidence_level, 'name') else str(analysis.confidence_level)
        print(f"    -> Category: {categories}")
        print(f"    -> Confidence: {conf_name} ({analysis.confidence_score})")
        if analysis.matched_keywords:
            print(f"    → 키워드: {analysis.matched_keywords}")
        if analysis.requires_human_review:
            print(f"    [!] 검토 필요: {analysis.review_reason}")


def demo_kakaotalk(filepath: str = None):
    """카카오톡 파싱 데모"""
    print_header("카카오톡 파싱 + 법적 분석")

    if filepath and os.path.exists(filepath):
        print(f"파일: {filepath}")
    else:
        # 샘플 데이터 생성
        sample_content = """카카오톡 대화
저장한 날짜: 2023-05-10

------------------------------
2023년 5월 10일 수요일
------------------------------
오전 9:23, 홍길동 : 오늘 몇시에 와?
오전 9:25, 김영희 : 7시쯤 갈 것 같아
오전 9:30, 홍길동 : 어제 그 사람 또 만났어?
오전 9:31, 김영희 : 응 호텔에서 만났어
오전 9:32, 홍길동 : 뭐? 불륜이야?
오전 9:35, 김영희 : 아니야 오해야
오전 10:15, 홍길동 : 시어머니가 또 뭐라고 했어?
오전 10:16, 김영희 : 또 폭언했어. 너무 힘들어
오전 11:00, 홍길동 : 돈 문제는 어떻게 됐어?
오전 11:01, 김영희 : 도박으로 또 500만원 날렸대"""

        # 임시 파일 생성
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(sample_content)
            filepath = f.name
        print("샘플 데이터 사용")

    # 파싱
    parser = KakaoTalkParserV2()
    chunks, result = parser.parse_to_chunks(filepath, "demo_case", "demo_file")

    print(f"\n총 {len(chunks)}개 메시지 파싱됨")
    print(f"파싱된 라인: {result.parsed_lines}/{result.total_lines}")

    # 법적 분석
    analyzer = LegalAnalyzer(use_ai=False)
    analyzed_chunks = analyzer.analyze_batch(chunks)

    # 결과 출력
    for i, chunk in enumerate(analyzed_chunks, 1):
        print_chunk(chunk, i)

    # 통계
    stats = analyzer.get_summary_stats(analyzed_chunks)
    print_header("분석 통계")
    print(f"총 청크: {stats['total_chunks']}")
    print(f"카테고리별: {stats['category_counts']}")
    print(f"고가치 증거 (Level 4-5): {stats['high_value_count']}개")
    print(f"검토 필요: {stats['requires_review_count']}개")

    # 임시 파일 삭제
    if 'tempfile' in sys.modules:
        try:
            os.unlink(filepath)
        except OSError:
            pass

    return analyzed_chunks


def demo_pdf(filepath: str):
    """PDF 파싱 데모"""
    print_header("PDF 파싱")

    if not os.path.exists(filepath):
        print(f"파일을 찾을 수 없습니다: {filepath}")
        return None

    parser = PDFParserV2()
    chunks, result = parser.parse_to_chunks(filepath, "demo_case", "demo_file")

    print(f"파일: {result.file_name}")
    print(f"총 페이지: {result.total_pages}")
    print(f"파싱된 페이지: {result.parsed_pages}")
    print(f"빈 페이지: {result.empty_pages}")
    print(f"파일 해시: {result.file_hash[:16]}...")

    # 법적 분석
    analyzer = LegalAnalyzer(use_ai=False)
    analyzed_chunks = analyzer.analyze_batch(chunks)

    for i, chunk in enumerate(analyzed_chunks[:5], 1):  # 최대 5개
        print_chunk(chunk, i)

    if len(analyzed_chunks) > 5:
        print(f"\n... 외 {len(analyzed_chunks) - 5}개 페이지")

    return analyzed_chunks


def demo_image(filepath: str):
    """이미지 파싱 데모"""
    print_header("이미지 EXIF 추출")

    if not os.path.exists(filepath):
        print(f"파일을 찾을 수 없습니다: {filepath}")
        return None

    parser = ImageParserV2()
    chunks, result = parser.parse_to_chunks(filepath, "demo_case", "demo_file")

    print(f"파일: {result.file_name}")
    print(f"파일 해시: {result.file_hash[:16]}...")
    print(f"EXIF 존재: {result.has_exif}")
    print(f"GPS 존재: {result.has_gps}")

    if result.images:
        img = result.images[0]
        exif = img.exif

        if exif.datetime_original:
            print(f"촬영 시간: {exif.datetime_original}")
        if exif.gps_coordinates:
            print(f"촬영 위치: {exif.gps_coordinates.to_string()}")
            print(f"지도 URL: {exif.gps_coordinates.to_map_url()}")
        if exif.device_info:
            print(f"촬영 기기: {exif.device_info.to_string()}")

    for i, chunk in enumerate(chunks, 1):
        print_chunk(chunk, i)

    return chunks


def main():
    print("\n" + "[ AI Worker V2 Pipeline Demo ]".center(60))
    print("=" * 60)

    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        ext = Path(filepath).suffix.lower()

        if ext == '.txt':
            demo_kakaotalk(filepath)
        elif ext == '.pdf':
            demo_pdf(filepath)
        elif ext in ['.jpg', '.jpeg', '.png']:
            demo_image(filepath)
        else:
            print(f"지원하지 않는 파일 형식: {ext}")
            print("지원 형식: .txt (카카오톡), .pdf, .jpg/.png (이미지)")
    else:
        # 샘플 데이터로 카카오톡 데모
        demo_kakaotalk()

    print("\n" + "=" * 60)
    print("  데모 완료!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
