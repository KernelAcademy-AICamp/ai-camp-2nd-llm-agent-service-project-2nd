"""
Evidence File Schema
증거 파일 메타데이터 - 무결성, EXIF, 파싱 상태 포함

파일 단위의 메타데이터를 관리하며, 법적 무결성 증명을 위한 해시값 포함
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import uuid

from .source_location import FileType


class ParsingStatus(str, Enum):
    """파싱 상태"""
    PENDING = "pending"  # 대기 중
    PROCESSING = "processing"  # 처리 중
    SUCCESS = "success"  # 성공
    PARTIAL = "partial"  # 부분 성공 (일부 오류)
    FAILED = "failed"  # 실패


class FileMetadata(BaseModel):
    """
    파일 메타데이터 (EXIF, 해시 등)

    이미지의 경우 EXIF 정보를 포함하여 촬영 시간/장소 증명
    모든 파일에 해시값을 생성하여 무결성 증명
    """

    # ========================================
    # 무결성 정보
    # ========================================
    file_hash_sha256: str = Field(
        ...,
        description="SHA-256 해시값 (무결성 증명용)"
    )

    file_size_bytes: int = Field(
        ...,
        ge=0,
        description="파일 크기 (바이트)"
    )

    # ========================================
    # EXIF 정보 (이미지용)
    # ========================================
    exif_datetime: Optional[datetime] = Field(
        None,
        description="EXIF 촬영 시간"
    )

    exif_gps_latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="EXIF GPS 위도"
    )

    exif_gps_longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="EXIF GPS 경도"
    )

    exif_gps_address: Optional[str] = Field(
        None,
        description="GPS 좌표의 주소 (역지오코딩 결과)"
    )

    exif_device_make: Optional[str] = Field(
        None,
        description="촬영 기기 제조사 (예: Apple)"
    )

    exif_device_model: Optional[str] = Field(
        None,
        description="촬영 기기 모델 (예: iPhone 14 Pro)"
    )

    # ========================================
    # 오디오/비디오 정보
    # ========================================
    duration_seconds: Optional[float] = Field(
        None,
        ge=0,
        description="재생 시간 (초)"
    )

    # ========================================
    # PDF 정보
    # ========================================
    total_pages: Optional[int] = Field(
        None,
        ge=1,
        description="총 페이지 수"
    )

    def has_gps(self) -> bool:
        """GPS 정보 존재 여부"""
        return (
            self.exif_gps_latitude is not None and
            self.exif_gps_longitude is not None
        )

    def get_gps_string(self) -> Optional[str]:
        """GPS 좌표 문자열"""
        if not self.has_gps():
            return None
        return f"{self.exif_gps_latitude:.6f}, {self.exif_gps_longitude:.6f}"


class EvidenceFile(BaseModel):
    """
    증거 파일

    파일 단위의 메타데이터를 관리
    하나의 파일은 여러 개의 EvidenceChunk를 포함할 수 있음

    Examples:
        카카오톡: 1개 파일 → 수백 개 메시지 청크
        PDF: 1개 파일 → 여러 페이지 청크
        이미지: 1개 파일 → 1개 청크 (전체 설명)
    """

    # ========================================
    # 식별자
    # ========================================
    file_id: str = Field(
        default_factory=lambda: f"file_{uuid.uuid4().hex[:12]}",
        description="파일 고유 ID"
    )

    case_id: str = Field(
        ...,
        description="소속 케이스 ID"
    )

    evidence_id: Optional[str] = Field(
        None,
        description="Backend에서 생성한 evidence_id (E2E 연동용)"
    )

    # ========================================
    # 파일 정보
    # ========================================
    filename: str = Field(
        ...,
        description="원본 파일명"
    )

    file_type: FileType = Field(
        ...,
        description="파일 유형"
    )

    s3_key: Optional[str] = Field(
        None,
        description="S3 저장 경로"
    )

    s3_raw_key: Optional[str] = Field(
        None,
        description="S3 원본 파일 경로 (보존용)"
    )

    # ========================================
    # 메타데이터
    # ========================================
    metadata: FileMetadata = Field(
        ...,
        description="파일 메타데이터 (해시, EXIF 등)"
    )

    # ========================================
    # 파싱 정보
    # ========================================
    parsing_status: ParsingStatus = Field(
        ParsingStatus.PENDING,
        description="파싱 상태"
    )

    parsed_at: Optional[datetime] = Field(
        None,
        description="파싱 완료 시간"
    )

    total_chunks: int = Field(
        0,
        ge=0,
        description="생성된 청크 수"
    )

    # ========================================
    # 오류 정보
    # ========================================
    parsing_errors: List[str] = Field(
        default_factory=list,
        description="파싱 중 발생한 오류 메시지들"
    )

    skipped_lines: List[int] = Field(
        default_factory=list,
        description="파싱 실패한 라인 번호들 (카카오톡용)"
    )

    # ========================================
    # 타임스탬프
    # ========================================
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="레코드 생성 시간"
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="레코드 수정 시간"
    )

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
