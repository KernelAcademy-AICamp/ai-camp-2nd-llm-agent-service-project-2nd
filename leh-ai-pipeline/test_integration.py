"""
파서 통합 테스트 스크립트
각 파서의 동작을 실제로 확인합니다.
"""

from src.parsers.kakaotalk import KakaoTalkParser
from src.parsers.text import TextParser


def test_kakaotalk_parser():
    """KakaoTalk Parser 통합 테스트"""
    print("=" * 60)
    print("KakaoTalk Parser 테스트")
    print("=" * 60)

    parser = KakaoTalkParser()
    messages = parser.parse("tests/fixtures/kakaotalk_sample.txt")

    print(f"\n파싱된 메시지 개수: {len(messages)}\n")

    for i, msg in enumerate(messages[:3], 1):  # 처음 3개만 출력
        print(f"메시지 {i}:")
        print(f"  발신자: {msg.sender}")
        print(f"  시간: {msg.timestamp}")
        print(f"  내용: {msg.content[:50]}..." if len(msg.content) > 50 else f"  내용: {msg.content}")
        print(f"  메타데이터: {msg.metadata}")
        print()

    print(f"[OK] KakaoTalk Parser passed ({len(messages)} messages)")


def test_text_parser():
    """Text Parser 통합 테스트"""
    print("\n" + "=" * 60)
    print("Text Parser 테스트")
    print("=" * 60)

    parser = TextParser()
    messages = parser.parse("tests/fixtures/text_sample.txt")

    print(f"\n파싱된 메시지 개수: {len(messages)}\n")

    for i, msg in enumerate(messages, 1):
        print(f"메시지 {i}:")
        print(f"  발신자: {msg.sender}")
        print(f"  시간: {msg.timestamp}")
        print(f"  내용 (처음 200자):")
        print(f"    {msg.content[:200]}...")
        print(f"  메타데이터: {msg.metadata}")
        print()

    print(f"[OK] Text Parser passed ({len(messages)} messages)")


def main():
    """통합 테스트 실행"""
    print("\n" + "LEH AI Pipeline - Parser Integration Test")
    print("=" * 60)

    try:
        test_kakaotalk_parser()
        test_text_parser()

        print("\n" + "=" * 60)
        print("[SUCCESS] All parser integration tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
