"""
Image Parser V2
이미지 파서 - 법적 증거용

핵심 기능:
- EXIF 메타데이터 추출 (촬영 일시, GPS, 기기 정보)
- 파일 해시 (무결성 증명)
- 이미지 인덱스 추적 (다중 이미지 증거)
- OCR 텍스트 추출 (선택적)
"""

import hashlib
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from src.schemas import (
    SourceLocation,
    FileType,
    EvidenceChunk,
    LegalAnalysis,
    FileMetadata,
)


@dataclass
class GPSCoordinates:
    """GPS 좌표"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None

    def to_string(self) -> str:
        """좌표 문자열 변환"""
        alt_str = f", 고도 {self.altitude:.1f}m" if self.altitude else ""
        return f"{self.latitude:.6f}, {self.longitude:.6f}{alt_str}"

    def to_map_url(self) -> str:
        """Google Maps URL"""
        return f"https://maps.google.com/?q={self.latitude},{self.longitude}"


@dataclass
class DeviceInfo:
    """촬영 기기 정보"""
    make: Optional[str] = None  # 제조사 (Apple, Samsung)
    model: Optional[str] = None  # 모델명 (iPhone 14 Pro)
    software: Optional[str] = None  # 소프트웨어 버전

    def to_string(self) -> str:
        """기기 정보 문자열"""
        parts = []
        if self.make:
            parts.append(self.make)
        if self.model:
            parts.append(self.model)
        if self.software:
            parts.append(f"(SW: {self.software})")
        return " ".join(parts) if parts else "Unknown Device"


@dataclass
class EXIFMetadata:
    """EXIF 메타데이터"""
    datetime_original: Optional[datetime] = None  # 원본 촬영 시간
    datetime_digitized: Optional[datetime] = None  # 디지털화 시간
    gps_coordinates: Optional[GPSCoordinates] = None
    device_info: Optional[DeviceInfo] = None

    # 추가 정보
    orientation: Optional[int] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    exposure_time: Optional[str] = None
    f_number: Optional[float] = None
    iso_speed: Optional[int] = None

    # 원본 EXIF 딕셔너리 (검증용)
    raw_exif: Dict[str, Any] = field(default_factory=dict)

    def has_location(self) -> bool:
        """위치 정보 존재 여부"""
        return self.gps_coordinates is not None

    def has_timestamp(self) -> bool:
        """촬영 시간 존재 여부"""
        return self.datetime_original is not None


@dataclass
class ParsedImage:
    """파싱된 이미지"""
    file_name: str
    image_index: int  # 파일 내 이미지 번호 (보통 1)
    file_hash: str
    file_size_bytes: int
    exif: EXIFMetadata
    ocr_text: Optional[str] = None  # OCR 추출 텍스트 (선택적)


@dataclass
class ImageParsingResult:
    """이미지 파싱 결과"""
    images: List[ParsedImage]
    file_name: str
    total_images: int
    has_exif: bool
    has_gps: bool
    file_hash: str
    file_size_bytes: int


class ImageParserV2:
    """
    이미지 파서 V2

    EXIF 메타데이터를 추출하고,
    법적 증거로 활용 가능한 형식으로 변환합니다.

    Usage:
        parser = ImageParserV2()
        result = parser.parse("photo.jpg")

        if result.has_gps:
            print(f"촬영 위치: {result.images[0].exif.gps_coordinates.to_string()}")
    """

    def __init__(self, extract_ocr: bool = False):
        """
        Args:
            extract_ocr: OCR 텍스트 추출 여부 (기본: False)
        """
        self.extract_ocr = extract_ocr

    def parse(self, filepath: str) -> ImageParsingResult:
        """
        이미지 파일 파싱

        Args:
            filepath: 이미지 파일 경로

        Returns:
            ImageParsingResult: 파싱 결과

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # 파일 해시 및 크기
        file_hash = self._calculate_file_hash(filepath)
        file_size = path.stat().st_size

        # 이미지 열기
        try:
            image = Image.open(filepath)
        except Exception as e:
            raise ValueError(f"Failed to open image: {e}")

        # EXIF 추출
        exif_data = self._extract_exif(image)

        # OCR 추출 (선택적)
        ocr_text = None
        if self.extract_ocr:
            ocr_text = self._extract_ocr_text(image)

        parsed_image = ParsedImage(
            file_name=path.name,
            image_index=1,  # 단일 이미지
            file_hash=file_hash,
            file_size_bytes=file_size,
            exif=exif_data,
            ocr_text=ocr_text
        )

        return ImageParsingResult(
            images=[parsed_image],
            file_name=path.name,
            total_images=1,
            has_exif=bool(exif_data.raw_exif),
            has_gps=exif_data.has_location(),
            file_hash=file_hash,
            file_size_bytes=file_size
        )

    def parse_multiple(self, filepaths: List[str]) -> List[ImageParsingResult]:
        """
        여러 이미지 파일 파싱 (인덱스 부여)

        Args:
            filepaths: 이미지 파일 경로 리스트

        Returns:
            List[ImageParsingResult]: 파싱 결과 리스트
        """
        results = []
        for idx, filepath in enumerate(filepaths, start=1):
            result = self.parse(filepath)
            # 이미지 인덱스 업데이트
            if result.images:
                result.images[0].image_index = idx
            results.append(result)
        return results

    def parse_to_chunks(
        self,
        filepath: str,
        case_id: str,
        file_id: str,
        image_index: int = 1
    ) -> Tuple[List[EvidenceChunk], ImageParsingResult]:
        """
        파싱 후 EvidenceChunk로 변환

        Args:
            filepath: 파일 경로
            case_id: 케이스 ID
            file_id: 파일 ID
            image_index: 이미지 인덱스 (여러 이미지 중 몇 번째인지)

        Returns:
            Tuple[List[EvidenceChunk], ImageParsingResult]: 청크 리스트와 파싱 결과
        """
        result = self.parse(filepath)
        chunks: List[EvidenceChunk] = []

        for img in result.images:
            # 원본 위치 정보
            source_location = SourceLocation(
                file_name=result.file_name,
                file_type=FileType.IMAGE,
                image_index=image_index
            )

            # 내용 구성
            content_parts = []

            # EXIF 정보 포함
            if img.exif.datetime_original:
                content_parts.append(f"촬영일시: {img.exif.datetime_original.strftime('%Y-%m-%d %H:%M:%S')}")

            if img.exif.has_location():
                coords = img.exif.gps_coordinates
                content_parts.append(f"촬영위치: {coords.to_string()}")

            if img.exif.device_info:
                content_parts.append(f"촬영기기: {img.exif.device_info.to_string()}")

            if img.ocr_text:
                content_parts.append(f"OCR 텍스트: {img.ocr_text}")

            content = "\n".join(content_parts) if content_parts else f"[이미지 {image_index}]"

            # 내용 해시
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

            # 타임스탬프: EXIF 촬영시간 또는 현재 시간
            timestamp = img.exif.datetime_original or datetime.now()

            chunk = EvidenceChunk(
                file_id=file_id,
                case_id=case_id,
                source_location=source_location,
                content=content,
                content_hash=content_hash,
                sender="Image",  # 이미지는 발신자 개념 없음
                timestamp=timestamp,
                legal_analysis=LegalAnalysis(),
                extra_metadata={
                    "image_index": image_index,
                    "has_exif": result.has_exif,
                    "has_gps": result.has_gps,
                    "file_hash": img.file_hash,
                    "device_info": img.exif.device_info.to_string() if img.exif.device_info else None,
                    "gps_url": img.exif.gps_coordinates.to_map_url() if img.exif.gps_coordinates else None
                }
            )
            chunks.append(chunk)

        return chunks, result

    def get_file_metadata(self, filepath: str) -> FileMetadata:
        """
        이미지 파일 메타데이터 추출

        Args:
            filepath: 파일 경로

        Returns:
            FileMetadata: 파일 메타데이터
        """
        path = Path(filepath)
        file_hash = self._calculate_file_hash(filepath)
        file_size = path.stat().st_size

        return FileMetadata(
            file_hash_sha256=file_hash,
            file_size_bytes=file_size,
            total_pages=1  # 이미지는 1페이지
        )

    def _extract_exif(self, image: Image.Image) -> EXIFMetadata:
        """EXIF 메타데이터 추출"""
        exif_data = EXIFMetadata()

        try:
            # PIL EXIF 추출
            raw_exif = image._getexif()
            if not raw_exif:
                return exif_data

            # 태그 이름으로 변환
            decoded_exif = {}
            for tag_id, value in raw_exif.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                decoded_exif[tag_name] = value

            exif_data.raw_exif = decoded_exif

            # 촬영 시간
            if "DateTimeOriginal" in decoded_exif:
                try:
                    dt_str = decoded_exif["DateTimeOriginal"]
                    exif_data.datetime_original = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                except (ValueError, TypeError):
                    pass

            if "DateTimeDigitized" in decoded_exif:
                try:
                    dt_str = decoded_exif["DateTimeDigitized"]
                    exif_data.datetime_digitized = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                except (ValueError, TypeError):
                    pass

            # 기기 정보
            device = DeviceInfo()
            if "Make" in decoded_exif:
                device.make = str(decoded_exif["Make"]).strip()
            if "Model" in decoded_exif:
                device.model = str(decoded_exif["Model"]).strip()
            if "Software" in decoded_exif:
                device.software = str(decoded_exif["Software"]).strip()

            if device.make or device.model:
                exif_data.device_info = device

            # GPS 정보
            if "GPSInfo" in decoded_exif:
                gps_info = decoded_exif["GPSInfo"]
                gps_coords = self._parse_gps_info(gps_info)
                if gps_coords:
                    exif_data.gps_coordinates = gps_coords

            # 이미지 크기
            if "ExifImageWidth" in decoded_exif:
                exif_data.image_width = int(decoded_exif["ExifImageWidth"])
            if "ExifImageHeight" in decoded_exif:
                exif_data.image_height = int(decoded_exif["ExifImageHeight"])

            # 카메라 설정
            if "ExposureTime" in decoded_exif:
                exif_data.exposure_time = str(decoded_exif["ExposureTime"])
            if "FNumber" in decoded_exif:
                try:
                    exif_data.f_number = float(decoded_exif["FNumber"])
                except (ValueError, TypeError):
                    pass
            if "ISOSpeedRatings" in decoded_exif:
                try:
                    exif_data.iso_speed = int(decoded_exif["ISOSpeedRatings"])
                except (ValueError, TypeError):
                    pass

            if "Orientation" in decoded_exif:
                try:
                    exif_data.orientation = int(decoded_exif["Orientation"])
                except (ValueError, TypeError):
                    pass

        except Exception:
            # EXIF 추출 실패해도 계속 진행
            pass

        return exif_data

    def _parse_gps_info(self, gps_info: dict) -> Optional[GPSCoordinates]:
        """GPS 정보 파싱"""
        try:
            # GPS 태그 디코딩
            gps_data = {}
            for tag_id, value in gps_info.items():
                tag_name = GPSTAGS.get(tag_id, str(tag_id))
                gps_data[tag_name] = value

            # 위도
            lat = None
            if "GPSLatitude" in gps_data and "GPSLatitudeRef" in gps_data:
                lat = self._convert_to_degrees(gps_data["GPSLatitude"])
                if gps_data["GPSLatitudeRef"] == "S":
                    lat = -lat

            # 경도
            lon = None
            if "GPSLongitude" in gps_data and "GPSLongitudeRef" in gps_data:
                lon = self._convert_to_degrees(gps_data["GPSLongitude"])
                if gps_data["GPSLongitudeRef"] == "W":
                    lon = -lon

            if lat is not None and lon is not None:
                # 고도 (선택적)
                alt = None
                if "GPSAltitude" in gps_data:
                    try:
                        alt = float(gps_data["GPSAltitude"])
                    except (ValueError, TypeError):
                        pass

                return GPSCoordinates(
                    latitude=lat,
                    longitude=lon,
                    altitude=alt
                )

        except Exception:
            pass

        return None

    def _convert_to_degrees(self, value) -> float:
        """GPS 좌표를 도(degrees)로 변환"""
        try:
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        except (TypeError, IndexError, ValueError):
            return 0.0

    def _extract_ocr_text(self, image: Image.Image) -> Optional[str]:
        """OCR 텍스트 추출 (선택적)"""
        try:
            import pytesseract
            # 그레이스케일 변환
            gray = image.convert('L')
            text = pytesseract.image_to_string(gray, lang='kor+eng')
            return text.strip() if text.strip() else None
        except ImportError:
            # pytesseract 미설치
            return None
        except Exception:
            return None

    def _calculate_file_hash(self, filepath: str) -> str:
        """파일 SHA-256 해시 계산"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# 간편 함수
def parse_image(filepath: str) -> ImageParsingResult:
    """이미지 파일 파싱 (간편 함수)"""
    parser = ImageParserV2()
    return parser.parse(filepath)


def extract_exif(filepath: str) -> EXIFMetadata:
    """EXIF 메타데이터만 추출 (간편 함수)"""
    parser = ImageParserV2()
    result = parser.parse(filepath)
    if result.images:
        return result.images[0].exif
    return EXIFMetadata()
