"""
Image Vision Analysis 테스트 (TDD RED Phase)

Given: 이미지 파일
When: GPT-4o Vision API로 분석
Then: 감정, 맥락, 분위기 정보 추출
"""

import unittest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime
from pathlib import Path

from src.parsers.image_vision import ImageVisionParser, VisionAnalysis
from src.parsers.base import Message


class TestImageVisionParserInitialization(unittest.TestCase):
    """ImageVisionParser 초기화 테스트"""

    def test_parser_creation(self):
        """Given: ImageVisionParser 생성 요청
        When: ImageVisionParser() 호출
        Then: 인스턴스 생성 성공"""
        parser = ImageVisionParser()
        self.assertIsNotNone(parser)

    def test_parser_is_base_parser(self):
        """Given: ImageVisionParser 인스턴스
        When: BaseParser 상속 확인
        Then: isinstance(parser, BaseParser) == True"""
        from src.parsers.base import BaseParser
        parser = ImageVisionParser()
        self.assertIsInstance(parser, BaseParser)


class TestVisionAnalysisDataModel(unittest.TestCase):
    """VisionAnalysis 데이터 모델 테스트"""

    def test_vision_analysis_creation(self):
        """Given: VisionAnalysis 생성
        When: 필수 필드 제공
        Then: 인스턴스 생성 성공"""
        analysis = VisionAnalysis(
            emotions=["happy", "excited"],
            context="두 사람이 카페에서 대화하는 장면",
            atmosphere="밝고 편안한 분위기",
            confidence=0.85
        )
        self.assertEqual(analysis.emotions, ["happy", "excited"])
        self.assertEqual(analysis.confidence, 0.85)

    def test_vision_analysis_default_values(self):
        """Given: VisionAnalysis 기본값 생성
        When: 선택 필드 없이 생성
        Then: 기본값 적용"""
        analysis = VisionAnalysis()
        self.assertEqual(analysis.emotions, [])
        self.assertEqual(analysis.context, "")
        self.assertEqual(analysis.atmosphere, "")
        self.assertEqual(analysis.confidence, 0.0)


class TestVisionAPIIntegration(unittest.TestCase):
    """GPT-4o Vision API 통합 테스트"""

    @patch('src.parsers.image_vision.openai')
    @patch('src.parsers.image_vision.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake image data')
    def test_analyze_image_with_vision(self, mock_file, mock_path, mock_openai):
        """Given: 이미지 파일
        When: GPT-4o Vision API로 분석
        Then: VisionAnalysis 반환"""
        mock_path.return_value.exists.return_value = True

        # Mock OpenAI Vision API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"emotions": ["happy"], "context": "사람이 웃고 있음", "atmosphere": "밝은 분위기"}'
        mock_openai.chat.completions.create.return_value = mock_response

        parser = ImageVisionParser()
        analysis = parser.analyze_vision("test.jpg")

        self.assertIsInstance(analysis, VisionAnalysis)
        self.assertIn("happy", analysis.emotions)

    @patch('src.parsers.image_vision.openai')
    @patch('src.parsers.image_vision.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake image data')
    def test_vision_api_called_correctly(self, mock_file, mock_path, mock_openai):
        """Given: 이미지 분석 요청
        When: analyze_vision() 호출
        Then: OpenAI API가 올바른 파라미터로 호출됨"""
        mock_path.return_value.exists.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"emotions": [], "context": "", "atmosphere": ""}'
        mock_openai.chat.completions.create.return_value = mock_response

        parser = ImageVisionParser()
        parser.analyze_vision("test.jpg")

        # Verify OpenAI API was called
        mock_openai.chat.completions.create.assert_called_once()
        call_args = mock_openai.chat.completions.create.call_args

        # Check model is gpt-4o or gpt-4-vision-preview
        self.assertIn('model', call_args.kwargs)
        self.assertIn('gpt-4', call_args.kwargs['model'].lower())


class TestEmotionDetection(unittest.TestCase):
    """감정 분석 테스트"""

    @patch('src.parsers.image_vision.openai')
    @patch('src.parsers.image_vision.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'image data')
    def test_detect_happy_emotion(self, mock_file, mock_path, mock_openai):
        """Given: 기쁜 감정의 이미지
        When: analyze_vision() 호출
        Then: emotions에 'happy' 포함"""
        mock_path.return_value.exists.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"emotions": ["happy", "joyful"], "context": "웃는 얼굴", "atmosphere": "긍정적"}'
        mock_openai.chat.completions.create.return_value = mock_response

        parser = ImageVisionParser()
        analysis = parser.analyze_vision("happy_face.jpg")

        self.assertIn("happy", analysis.emotions)
        self.assertGreater(len(analysis.emotions), 0)

    @patch('src.parsers.image_vision.openai')
    @patch('src.parsers.image_vision.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'image data')
    def test_detect_sad_emotion(self, mock_file, mock_path, mock_openai):
        """Given: 슬픈 감정의 이미지
        When: analyze_vision() 호출
        Then: emotions에 'sad' 포함"""
        mock_path.return_value.exists.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"emotions": ["sad", "depressed"], "context": "우는 모습", "atmosphere": "어두운 분위기"}'
        mock_openai.chat.completions.create.return_value = mock_response

        parser = ImageVisionParser()
        analysis = parser.analyze_vision("sad_face.jpg")

        self.assertIn("sad", analysis.emotions)

    @patch('src.parsers.image_vision.openai')
    @patch('src.parsers.image_vision.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'image data')
    def test_detect_angry_emotion(self, mock_file, mock_path, mock_openai):
        """Given: 화난 감정의 이미지
        When: analyze_vision() 호출
        Then: emotions에 'angry' 포함"""
        mock_path.return_value.exists.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"emotions": ["angry", "frustrated"], "context": "화난 표정", "atmosphere": "긴장된 분위기"}'
        mock_openai.chat.completions.create.return_value = mock_response

        parser = ImageVisionParser()
        analysis = parser.analyze_vision("angry_face.jpg")

        self.assertIn("angry", analysis.emotions)


class TestContextAnalysis(unittest.TestCase):
    """맥락 분석 테스트"""

    @patch('src.parsers.image_vision.openai')
    @patch('src.parsers.image_vision.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'image data')
    def test_analyze_scene_context(self, mock_file, mock_path, mock_openai):
        """Given: 특정 장면의 이미지
        When: analyze_vision() 호출
        Then: context에 장면 설명 포함"""
        mock_path.return_value.exists.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"emotions": ["neutral"], "context": "레스토랑에서 두 사람이 식사하는 장면", "atmosphere": "로맨틱한 분위기"}'
        mock_openai.chat.completions.create.return_value = mock_response

        parser = ImageVisionParser()
        analysis = parser.analyze_vision("restaurant.jpg")

        self.assertIn("레스토랑", analysis.context)
        self.assertGreater(len(analysis.context), 0)

    @patch('src.parsers.image_vision.openai')
    @patch('src.parsers.image_vision.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'image data')
    def test_analyze_object_detection(self, mock_file, mock_path, mock_openai):
        """Given: 특정 객체가 있는 이미지
        When: analyze_vision() 호출
        Then: context에 객체 정보 포함"""
        mock_path.return_value.exists.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"emotions": [], "context": "호텔 방 침대와 가방이 보임", "atmosphere": "의심스러운 분위기"}'
        mock_openai.chat.completions.create.return_value = mock_response

        parser = ImageVisionParser()
        analysis = parser.analyze_vision("hotel_room.jpg")

        self.assertIn("호텔", analysis.context)


class TestAtmosphereAnalysis(unittest.TestCase):
    """분위기 분석 테스트"""

    @patch('src.parsers.image_vision.openai')
    @patch('src.parsers.image_vision.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'image data')
    def test_analyze_atmosphere(self, mock_file, mock_path, mock_openai):
        """Given: 특정 분위기의 이미지
        When: analyze_vision() 호출
        Then: atmosphere에 분위기 설명 포함"""
        mock_path.return_value.exists.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"emotions": ["tense"], "context": "심각한 대화 장면", "atmosphere": "긴장되고 불편한 분위기"}'
        mock_openai.chat.completions.create.return_value = mock_response

        parser = ImageVisionParser()
        analysis = parser.analyze_vision("tense_scene.jpg")

        self.assertIn("긴장", analysis.atmosphere)
        self.assertGreater(len(analysis.atmosphere), 0)


class TestCombinedOCRAndVision(unittest.TestCase):
    """OCR + Vision 통합 분석 테스트"""

    @patch('src.parsers.image_vision.openai')
    @patch('src.parsers.image_vision.pytesseract')
    @patch('src.parsers.image_vision.Image')
    @patch('src.parsers.image_vision.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'image data')
    def test_parse_with_ocr_and_vision(self, mock_file, mock_path, mock_image, mock_tesseract, mock_openai):
        """Given: 텍스트와 시각 정보가 있는 이미지
        When: parse() 호출 (OCR + Vision)
        Then: Message에 텍스트와 vision_analysis 모두 포함"""
        mock_path.return_value.exists.return_value = True

        # Mock OCR
        mock_img = MagicMock()
        mock_image.open.return_value = mock_img
        mock_img.convert.return_value = mock_img
        mock_tesseract.image_to_string.return_value = "외도 증거입니다"

        # Mock Vision API
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"emotions": ["suspicious"], "context": "호텔 방 사진", "atmosphere": "의심스러운 분위기"}'
        mock_openai.chat.completions.create.return_value = mock_response

        parser = ImageVisionParser()
        messages = parser.parse("evidence.jpg", include_vision=True)

        self.assertGreater(len(messages), 0)
        # First message should have vision_analysis metadata
        self.assertTrue(hasattr(messages[0], 'metadata') or 'vision_analysis' in str(messages[0]))


class TestEdgeCases(unittest.TestCase):
    """엣지 케이스 테스트"""

    @patch('src.parsers.image_vision.Path')
    def test_invalid_file_path(self, mock_path):
        """Given: 존재하지 않는 파일 경로
        When: analyze_vision() 호출
        Then: FileNotFoundError 발생"""
        mock_path.return_value.exists.return_value = False

        parser = ImageVisionParser()
        with self.assertRaises(FileNotFoundError):
            parser.analyze_vision("nonexistent.jpg")

    @patch('src.parsers.image_vision.openai')
    @patch('src.parsers.image_vision.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'image data')
    def test_vision_api_error_handling(self, mock_file, mock_path, mock_openai):
        """Given: Vision API 호출 중 에러
        When: analyze_vision() 호출
        Then: 적절한 예외 처리 또는 기본값 반환"""
        mock_path.return_value.exists.return_value = True

        # Mock API error
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        parser = ImageVisionParser()
        # Should either raise exception or return default VisionAnalysis
        try:
            analysis = parser.analyze_vision("test.jpg")
            # If it doesn't raise, check it returns valid default
            self.assertIsInstance(analysis, VisionAnalysis)
        except Exception as e:
            # If it raises, that's also acceptable
            self.assertIn("API", str(e))

    @patch('src.parsers.image_vision.openai')
    @patch('src.parsers.image_vision.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'image data')
    def test_malformed_json_response(self, mock_file, mock_path, mock_openai):
        """Given: Vision API가 잘못된 JSON 반환
        When: analyze_vision() 호출
        Then: 파싱 실패 시 기본값 반환 또는 예외"""
        mock_path.return_value.exists.return_value = True

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'Invalid JSON format'
        mock_openai.chat.completions.create.return_value = mock_response

        parser = ImageVisionParser()
        analysis = parser.analyze_vision("test.jpg")

        # Should return valid VisionAnalysis with defaults
        self.assertIsInstance(analysis, VisionAnalysis)


import pytest
import os
import tempfile


class TestImageVisionRealAPI:
    """
    ImageVisionParser Real API 테스트 (GPT-4o Vision)

    Given: 실제 이미지 파일
    When: Mock 없이 GPT-4o Vision API 호출
    Then: 실제 감정, 맥락, 분위기 분석 결과 반환

    NOTE: OPENAI_API_KEY 환경변수 필요
    """

    @pytest.fixture
    def test_image_path(self):
        """테스트용 이미지 생성 (PIL)"""
        from PIL import Image, ImageDraw

        # 임시 이미지 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            # 간단한 테스트 이미지 생성 (사람 얼굴 아이콘)
            img = Image.new('RGB', (200, 200), color='white')
            draw = ImageDraw.Draw(img)

            # 얼굴 윤곽
            draw.ellipse([40, 40, 160, 160], outline='black', width=2)
            # 눈
            draw.ellipse([70, 70, 90, 90], fill='black')
            draw.ellipse([110, 70, 130, 90], fill='black')
            # 입 (웃는 표정)
            draw.arc([70, 100, 130, 140], 0, 180, fill='black', width=2)

            img.save(f.name, 'JPEG')
            yield f.name

        # 테스트 후 정리
        if os.path.exists(f.name):
            os.unlink(f.name)

    @pytest.mark.real
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY 환경변수가 설정되지 않음"
    )
    def test_real_vision_analysis_returns_valid_result(self, test_image_path):
        """
        Given: 실제 이미지 파일 (간단한 얼굴 그림)
        When: GPT-4o Vision API로 분석 (Mock 없이)
        Then: VisionAnalysis 객체 반환 (emotions, context, atmosphere 포함)
        """
        parser = ImageVisionParser()

        # Real API 호출 (Mock 없음!)
        analysis = parser.analyze_vision(test_image_path)

        # 기본 검증
        assert analysis is not None
        assert isinstance(analysis, VisionAnalysis)

        # 분석 결과 검증
        assert analysis.context, "context가 비어있으면 안 됨"
        assert analysis.confidence > 0, "confidence가 0보다 커야 함"

        print(f"\n=== Real Vision API Result ===")
        print(f"Emotions: {analysis.emotions}")
        print(f"Context: {analysis.context}")
        print(f"Atmosphere: {analysis.atmosphere}")
        print(f"Confidence: {analysis.confidence}")

    @pytest.mark.real
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY 환경변수가 설정되지 않음"
    )
    def test_real_vision_analysis_emotions_list(self, test_image_path):
        """
        Given: 실제 이미지 파일
        When: GPT-4o Vision API로 분석
        Then: emotions가 리스트 형태로 반환
        """
        parser = ImageVisionParser()

        analysis = parser.analyze_vision(test_image_path)

        # emotions 검증
        assert isinstance(analysis.emotions, list)
        # GPT-4o는 이미지에서 감정을 추출해야 함 (빈 리스트도 유효)
        print(f"\nDetected emotions: {analysis.emotions}")

    @pytest.mark.real
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY 환경변수가 설정되지 않음"
    )
    def test_real_vision_analysis_confidence_range(self, test_image_path):
        """
        Given: 실제 이미지 파일
        When: GPT-4o Vision API로 분석
        Then: confidence가 0.0 ~ 1.0 범위
        """
        parser = ImageVisionParser()

        analysis = parser.analyze_vision(test_image_path)

        # confidence 범위 검증
        assert 0.0 <= analysis.confidence <= 1.0


if __name__ == '__main__':
    unittest.main()
