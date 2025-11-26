"""
Parser Demo Script
==================
각 파서를 직접 테스트해볼 수 있는 데모 스크립트입니다.

사용법:
    python demo_parsers.py

테스트 가능한 파서:
    1. PDFParser - PDF 파일 텍스트 추출
    2. ImageOCRParser - 이미지 OCR (Tesseract 필요)
    3. AudioParser - 오디오 STT (OpenAI API 키 필요)
    4. KakaoTalkParser - 카카오톡 대화 파싱
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from parsers.pdf_parser import PDFParser
from parsers.kakaotalk import KakaoTalkParser

# Optional imports (may fail if dependencies not installed)
try:
    from parsers.image_ocr import ImageOCRParser
    IMAGE_OCR_AVAILABLE = True
except ImportError:
    IMAGE_OCR_AVAILABLE = False

try:
    from parsers.audio_parser import AudioParser
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_messages(messages, max_content_length=200):
    """Print messages in a readable format"""
    if not messages:
        print("  (결과 없음)")
        return

    for i, msg in enumerate(messages, 1):
        content = msg.content
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."

        print(f"\n  [{i}] Sender: {msg.sender}")
        print(f"      Time: {msg.timestamp}")
        print(f"      Content: {content}")


def demo_pdf_parser():
    """PDF Parser 데모"""
    print_header("PDF Parser 데모")

    # 기본 테스트 파일
    test_file = Path(__file__).parent / "tests" / "fixtures" / "real_document.pdf"

    print(f"\n테스트 파일: {test_file}")

    if not test_file.exists():
        print("  [오류] 테스트 파일이 없습니다.")
        return

    parser = PDFParser()
    messages = parser.parse(str(test_file))

    print(f"\n추출된 페이지 수: {len(messages)}")
    print_messages(messages)

    # 사용자 파일 테스트
    print("\n" + "-" * 40)
    user_file = input("다른 PDF 파일 경로 입력 (Enter로 건너뛰기): ").strip()

    if user_file and Path(user_file).exists():
        messages = parser.parse(user_file)
        print(f"\n추출된 페이지 수: {len(messages)}")
        print_messages(messages)
    elif user_file:
        print(f"  [오류] 파일을 찾을 수 없습니다: {user_file}")


def demo_kakaotalk_parser():
    """KakaoTalk Parser 데모"""
    print_header("KakaoTalk Parser 데모")

    # 기본 테스트 파일
    test_file = Path(__file__).parent / "tests" / "fixtures" / "kakaotalk_sample.txt"

    print(f"\n테스트 파일: {test_file}")

    if not test_file.exists():
        print("  [오류] 테스트 파일이 없습니다.")
        return

    parser = KakaoTalkParser()
    messages = parser.parse(str(test_file))

    print(f"\n추출된 메시지 수: {len(messages)}")
    print_messages(messages[:10])  # 처음 10개만 표시

    if len(messages) > 10:
        print(f"\n  ... 외 {len(messages) - 10}개 메시지")

    # 사용자 파일 테스트
    print("\n" + "-" * 40)
    user_file = input("다른 카카오톡 파일 경로 입력 (Enter로 건너뛰기): ").strip()

    if user_file and Path(user_file).exists():
        messages = parser.parse(user_file)
        print(f"\n추출된 메시지 수: {len(messages)}")
        print_messages(messages[:10])
    elif user_file:
        print(f"  [오류] 파일을 찾을 수 없습니다: {user_file}")


def demo_image_ocr_parser():
    """Image OCR Parser 데모"""
    print_header("Image OCR Parser 데모")

    if not IMAGE_OCR_AVAILABLE:
        print("  [오류] ImageOCRParser를 불러올 수 없습니다.")
        print("  pytesseract 설치 필요: pip install pytesseract")
        return

    # Tesseract 설치 확인
    import shutil
    if not shutil.which('tesseract'):
        print("  [오류] Tesseract가 설치되어 있지 않습니다.")
        print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  Mac: brew install tesseract")
        print("  Linux: sudo apt install tesseract-ocr")
        return

    # 기본 테스트 파일
    test_file = Path(__file__).parent / "tests" / "fixtures" / "real_image.png"

    print(f"\n테스트 파일: {test_file}")

    if not test_file.exists():
        print("  [오류] 테스트 파일이 없습니다.")
        return

    parser = ImageOCRParser()
    messages = parser.parse(str(test_file))

    print(f"\n추출된 텍스트 라인 수: {len(messages)}")
    print_messages(messages)

    # 사용자 파일 테스트
    print("\n" + "-" * 40)
    user_file = input("다른 이미지 파일 경로 입력 (Enter로 건너뛰기): ").strip()

    if user_file and Path(user_file).exists():
        messages = parser.parse(user_file)
        print(f"\n추출된 텍스트 라인 수: {len(messages)}")
        print_messages(messages)
    elif user_file:
        print(f"  [오류] 파일을 찾을 수 없습니다: {user_file}")


def demo_audio_parser():
    """Audio Parser 데모"""
    print_header("Audio Parser 데모")

    if not AUDIO_AVAILABLE:
        print("  [오류] AudioParser를 불러올 수 없습니다.")
        print("  openai 설치 필요: pip install openai")
        return

    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("  [오류] OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("  설정 방법: set OPENAI_API_KEY=sk-xxx (Windows)")
        print("            export OPENAI_API_KEY=sk-xxx (Linux/Mac)")
        return

    # 기본 테스트 파일
    test_file = Path(__file__).parent / "tests" / "fixtures" / "real_audio.mp3"

    print(f"\n테스트 파일: {test_file}")

    if not test_file.exists():
        print("  [오류] 테스트 파일이 없습니다.")
        return

    print("\n  Whisper API 호출 중... (약 10-30초 소요)")

    parser = AudioParser()
    messages = parser.parse(str(test_file))

    print(f"\n추출된 세그먼트 수: {len(messages)}")
    print_messages(messages)

    # 사용자 파일 테스트
    print("\n" + "-" * 40)
    user_file = input("다른 오디오 파일 경로 입력 (Enter로 건너뛰기): ").strip()

    if user_file and Path(user_file).exists():
        print("\n  Whisper API 호출 중...")
        messages = parser.parse(user_file)
        print(f"\n추출된 세그먼트 수: {len(messages)}")
        print_messages(messages)
    elif user_file:
        print(f"  [오류] 파일을 찾을 수 없습니다: {user_file}")


def main():
    """메인 메뉴"""
    while True:
        print_header("Parser Demo - 메인 메뉴")
        print("""
  테스트할 파서를 선택하세요:

  [1] PDF Parser      - PDF 파일 텍스트 추출
  [2] KakaoTalk Parser - 카카오톡 대화 파싱
  [3] Image OCR Parser - 이미지 OCR (Tesseract 필요)
  [4] Audio Parser    - 오디오 STT (OpenAI API 필요)

  [0] 종료
        """)

        choice = input("선택 (0-4): ").strip()

        if choice == "0":
            print("\n데모를 종료합니다.")
            break
        elif choice == "1":
            demo_pdf_parser()
        elif choice == "2":
            demo_kakaotalk_parser()
        elif choice == "3":
            demo_image_ocr_parser()
        elif choice == "4":
            demo_audio_parser()
        else:
            print("\n  [오류] 잘못된 선택입니다. 0-4 사이의 숫자를 입력하세요.")

        input("\n계속하려면 Enter를 누르세요...")


if __name__ == "__main__":
    main()
