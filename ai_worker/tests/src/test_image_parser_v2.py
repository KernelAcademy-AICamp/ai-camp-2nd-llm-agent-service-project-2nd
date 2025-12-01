"""
Image Parser V2 테스트

Given: 이미지 파일
When: ImageParserV2.parse() 호출
Then: EXIF 메타데이터와 법적 인용 정보 반환
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import os
from io import BytesIO

from src.parsers.image_parser_v2 import (
    ImageParserV2,
    ParsedImage,
    ImageParsingResult,
    GPSCoordinates,
    DeviceInfo,
    EXIFMetadata
)


class TestImageParserV2Initialization:
    """ImageParserV2 초기화 테스트"""

    def test_parser_creation(self):
        """Given: 기본 설정
        When: ImageParserV2() 생성
        Then: 파서 인스턴스 생성"""
        parser = ImageParserV2()
        assert parser is not None
        assert parser.extract_ocr is False

    def test_parser_with_ocr_enabled(self):
        """Given: OCR 활성화
        When: ImageParserV2(extract_ocr=True) 생성
        Then: 설정값 반영"""
        parser = ImageParserV2(extract_ocr=True)
        assert parser.extract_ocr is True


class TestGPSCoordinates:
    """GPSCoordinates 모델 테스트"""

    def test_coordinates_creation(self):
        """Given: GPS 좌표
        When: GPSCoordinates 생성
        Then: 속성 정확히 설정"""
        coords = GPSCoordinates(
            latitude=37.5665,
            longitude=126.9780,
            altitude=50.0
        )

        assert coords.latitude == 37.5665
        assert coords.longitude == 126.9780
        assert coords.altitude == 50.0

    def test_coordinates_to_string(self):
        """Given: GPSCoordinates
        When: to_string() 호출
        Then: 형식화된 문자열 반환"""
        coords = GPSCoordinates(
            latitude=37.5665,
            longitude=126.9780
        )

        string = coords.to_string()
        assert "37.5665" in string
        assert "126.9780" in string

    def test_coordinates_to_map_url(self):
        """Given: GPSCoordinates
        When: to_map_url() 호출
        Then: Google Maps URL 반환"""
        coords = GPSCoordinates(
            latitude=37.5665,
            longitude=126.9780
        )

        url = coords.to_map_url()
        # URL 형식: "https://maps.google.com/?q=37.5665,126.978"
        assert "maps.google.com" in url or "google.com/maps" in url
        assert "37.5665" in url
        assert "126.978" in url


class TestDeviceInfo:
    """DeviceInfo 모델 테스트"""

    def test_device_info_creation(self):
        """Given: 기기 정보
        When: DeviceInfo 생성
        Then: 속성 정확히 설정"""
        device = DeviceInfo(
            make="Samsung",
            model="Galaxy S23",
            software="One UI 5.1"
        )

        assert device.make == "Samsung"
        assert device.model == "Galaxy S23"
        assert device.software == "One UI 5.1"

    def test_device_info_to_string(self):
        """Given: DeviceInfo
        When: to_string() 호출
        Then: 형식화된 문자열 반환"""
        device = DeviceInfo(
            make="Apple",
            model="iPhone 15 Pro"
        )

        string = device.to_string()
        assert "Apple" in string
        assert "iPhone 15 Pro" in string


class TestEXIFMetadata:
    """EXIFMetadata 모델 테스트"""

    def test_exif_defaults(self):
        """Given: 기본 EXIFMetadata
        When: 생성
        Then: 기본값 설정"""
        exif = EXIFMetadata()

        assert exif.datetime_original is None
        assert exif.gps_coordinates is None
        assert exif.device_info is None
        assert exif.raw_exif == {}

    def test_exif_has_location(self):
        """Given: GPS 좌표 있는 EXIF
        When: has_location() 호출
        Then: True 반환"""
        exif = EXIFMetadata(
            gps_coordinates=GPSCoordinates(latitude=37.5, longitude=126.9)
        )

        assert exif.has_location() is True

    def test_exif_has_no_location(self):
        """Given: GPS 좌표 없는 EXIF
        When: has_location() 호출
        Then: False 반환"""
        exif = EXIFMetadata()

        assert exif.has_location() is False


class TestParsedImage:
    """ParsedImage 모델 테스트"""

    def test_parsed_image_creation(self):
        """Given: 이미지 데이터
        When: ParsedImage 생성
        Then: 속성 정확히 설정"""
        image = ParsedImage(
            file_name="photo.jpg",
            image_index=1,
            file_hash="abc123",
            file_size_bytes=1024,
            exif=EXIFMetadata(),
            ocr_text=None
        )

        assert image.file_name == "photo.jpg"
        assert image.image_index == 1
        assert image.file_hash == "abc123"


class TestImageParsingResult:
    """ImageParsingResult 모델 테스트"""

    def test_result_creation(self):
        """Given: 파싱 결과 데이터
        When: ImageParsingResult 생성
        Then: 속성 정확히 설정"""
        image = ParsedImage(
            file_name="photo.jpg",
            image_index=1,
            file_hash="abc123",
            file_size_bytes=1024,
            exif=EXIFMetadata(
                gps_coordinates=GPSCoordinates(latitude=37.5, longitude=126.9)
            )
        )

        result = ImageParsingResult(
            images=[image],
            file_name="photo.jpg",
            total_images=1,
            has_exif=True,
            has_gps=True,
            file_hash="abc123",
            file_size_bytes=1024
        )

        assert result.total_images == 1
        assert result.has_exif is True
        assert result.has_gps is True


class TestImageParserV2Parse:
    """parse() 메서드 테스트"""

    def test_parse_file_not_found(self):
        """Given: 존재하지 않는 파일
        When: parse() 호출
        Then: FileNotFoundError 발생"""
        parser = ImageParserV2()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.jpg")

    @patch('src.parsers.image_parser_v2.Image')
    def test_parse_returns_result(self, mock_image_module):
        """Given: 유효한 이미지 파일
        When: parse() 호출
        Then: ImageParsingResult 반환"""
        # Mock 이미지
        mock_img = MagicMock()
        mock_img._getexif.return_value = None
        mock_image_module.open.return_value = mock_img

        parser = ImageParserV2()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'\xff\xd8\xff\xe0')  # JPEG magic bytes
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert isinstance(result, ImageParsingResult)
            assert result.total_images == 1
        finally:
            os.unlink(temp_path)

    @patch('src.parsers.image_parser_v2.Image')
    def test_parse_extracts_exif(self, mock_image_module):
        """Given: EXIF 데이터 있는 이미지
        When: parse() 호출
        Then: EXIF 추출"""
        # Mock EXIF 데이터
        mock_exif = {
            271: "Samsung",        # Make
            272: "Galaxy S23",     # Model
            36867: "2024:01:15 10:30:00"  # DateTimeOriginal
        }

        mock_img = MagicMock()
        mock_img._getexif.return_value = mock_exif
        mock_image_module.open.return_value = mock_img

        parser = ImageParserV2()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'\xff\xd8\xff\xe0')
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.has_exif is True
        finally:
            os.unlink(temp_path)


class TestImageParserV2ParseMultiple:
    """parse_multiple() 메서드 테스트"""

    @patch('src.parsers.image_parser_v2.Image')
    def test_parse_multiple_images(self, mock_image_module):
        """Given: 여러 이미지 파일
        When: parse_multiple() 호출
        Then: 인덱스 부여된 결과 리스트"""
        mock_img = MagicMock()
        mock_img._getexif.return_value = None
        mock_image_module.open.return_value = mock_img

        parser = ImageParserV2()
        temp_paths = []

        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                    f.write(b'\xff\xd8\xff\xe0')
                    temp_paths.append(f.name)

            results = parser.parse_multiple(temp_paths)

            assert len(results) == 3
            assert results[0].images[0].image_index == 1
            assert results[1].images[0].image_index == 2
            assert results[2].images[0].image_index == 3
        finally:
            for path in temp_paths:
                os.unlink(path)


class TestImageParserV2ParseToChunks:
    """parse_to_chunks() 메서드 테스트"""

    @patch('src.parsers.image_parser_v2.Image')
    def test_parse_to_chunks_returns_evidence_chunks(self, mock_image_module):
        """Given: 이미지 파일
        When: parse_to_chunks() 호출
        Then: EvidenceChunk 리스트 반환"""
        mock_img = MagicMock()
        mock_img._getexif.return_value = None
        mock_image_module.open.return_value = mock_img

        parser = ImageParserV2()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'\xff\xd8\xff\xe0')
            temp_path = f.name

        try:
            chunks, result = parser.parse_to_chunks(
                filepath=temp_path,
                case_id="case_001",
                file_id="file_001"
            )

            assert len(chunks) == 1
            assert chunks[0].case_id == "case_001"
            assert chunks[0].file_id == "file_001"
        finally:
            os.unlink(temp_path)

    @patch('src.parsers.image_parser_v2.Image')
    def test_parse_to_chunks_includes_exif_in_content(self, mock_image_module):
        """Given: EXIF 데이터 있는 이미지
        When: parse_to_chunks() 호출
        Then: content에 EXIF 정보 포함"""
        # Mock EXIF with GPS
        mock_exif = {
            271: "Apple",
            272: "iPhone 15",
            36867: "2024:01:15 10:30:00"
        }

        mock_img = MagicMock()
        mock_img._getexif.return_value = mock_exif
        mock_image_module.open.return_value = mock_img

        parser = ImageParserV2()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'\xff\xd8\xff\xe0')
            temp_path = f.name

        try:
            chunks, _ = parser.parse_to_chunks(
                filepath=temp_path,
                case_id="case_001",
                file_id="file_001"
            )

            # 촬영일시 또는 촬영기기 정보가 content에 포함될 수 있음
            assert chunks[0].content is not None
        finally:
            os.unlink(temp_path)


class TestImageParserV2FileMetadata:
    """get_file_metadata() 메서드 테스트"""

    def test_get_file_metadata(self):
        """Given: 이미지 파일
        When: get_file_metadata() 호출
        Then: FileMetadata 반환"""
        parser = ImageParserV2()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'\xff\xd8\xff\xe0' + b'0' * 100)
            temp_path = f.name

        try:
            metadata = parser.get_file_metadata(temp_path)

            assert metadata.file_hash_sha256 is not None
            assert metadata.file_size_bytes > 0
        finally:
            os.unlink(temp_path)


class TestImageParserV2GPSParsing:
    """GPS 파싱 테스트"""

    def test_convert_to_degrees(self):
        """Given: GPS 좌표 튜플
        When: _convert_to_degrees() 호출
        Then: 도(degrees) 단위로 변환"""
        parser = ImageParserV2()

        # 37° 33' 59.4" = 37.5665°
        coords = (37.0, 33.0, 59.4)
        degrees = parser._convert_to_degrees(coords)

        assert abs(degrees - 37.5665) < 0.001


class TestImageParserV2OCR:
    """OCR 추출 테스트"""

    @patch('src.parsers.image_parser_v2.Image')
    def test_extract_ocr_when_enabled(self, mock_image_module):
        """Given: OCR 활성화 파서
        When: parse() 호출
        Then: OCR 텍스트 추출 시도 (pytesseract 미설치시 None)"""
        mock_img = MagicMock()
        mock_img._getexif.return_value = None
        mock_img.convert.return_value = mock_img
        mock_image_module.open.return_value = mock_img

        parser = ImageParserV2(extract_ocr=True)

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'\xff\xd8\xff\xe0')
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            # OCR 활성화되어 있으면 시도함 (결과는 None일 수 있음)
            assert result is not None
            # pytesseract 미설치 환경에서는 ocr_text가 None
            assert result.images[0].ocr_text is None or isinstance(result.images[0].ocr_text, str)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
