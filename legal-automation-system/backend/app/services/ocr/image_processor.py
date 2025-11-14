"""
이미지 처리 및 전처리 모듈
"""

import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import asyncio
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from skimage import filters, morphology, measure
from scipy import ndimage

from app.core.logging import logger


class ImageProcessor:
    """이미지 전처리 및 향상 처리기"""

    def __init__(self):
        """이미지 프로세서 초기화"""
        self.preprocessing_pipeline = [
            'denoise',
            'deskew',
            'remove_borders',
            'binarize',
            'enhance_text'
        ]

    async def preprocess_for_ocr(
        self,
        image: np.ndarray,
        document_type: str = "general"
    ) -> np.ndarray:
        """
        OCR을 위한 이미지 전처리

        Args:
            image: 입력 이미지
            document_type: 문서 타입 (general, handwritten, printed, mixed)

        Returns:
            전처리된 이미지
        """
        # 문서 타입별 전처리 파이프라인 선택
        if document_type == "handwritten":
            processed = await self._preprocess_handwritten(image)
        elif document_type == "printed":
            processed = await self._preprocess_printed(image)
        elif document_type == "mixed":
            processed = await self._preprocess_mixed(image)
        else:
            processed = await self._preprocess_general(image)

        return processed

    async def _preprocess_general(self, image: np.ndarray) -> np.ndarray:
        """일반 문서 전처리"""
        # 그레이스케일 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 노이즈 제거
        denoised = await self._denoise(gray)

        # 기울기 보정
        deskewed = await self._deskew(denoised)

        # 테두리 제거
        borderless = await self._remove_borders(deskewed)

        # 이진화
        binary = await self._binarize(borderless)

        # 텍스트 향상
        enhanced = await self._enhance_text(binary)

        return enhanced

    async def _preprocess_printed(self, image: np.ndarray) -> np.ndarray:
        """인쇄 문서 전처리"""
        # 그레이스케일 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 대비 향상
        enhanced = await self._enhance_contrast(gray)

        # 샤프닝
        sharpened = await self._sharpen(enhanced)

        # 노이즈 제거 (약하게)
        denoised = cv2.fastNlMeansDenoising(sharpened, h=3)

        # 기울기 보정
        deskewed = await self._deskew(denoised)

        # Otsu 이진화
        _, binary = cv2.threshold(deskewed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    async def _preprocess_handwritten(self, image: np.ndarray) -> np.ndarray:
        """손글씨 문서 전처리"""
        # 그레이스케일 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 배경 제거
        background_removed = await self._remove_background(gray)

        # 펜 자국 향상
        enhanced = await self._enhance_pen_strokes(background_removed)

        # 적응형 이진화
        binary = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        # 모폴로지 연산으로 끊어진 획 연결
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        connected = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return connected

    async def _preprocess_mixed(self, image: np.ndarray) -> np.ndarray:
        """혼합 문서 (인쇄 + 손글씨) 전처리"""
        # 그레이스케일 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 영역 분할
        printed_regions, handwritten_regions = await self._segment_regions(gray)

        # 각 영역별 처리
        result = np.zeros_like(gray)

        for region in printed_regions:
            x, y, w, h = region
            roi = gray[y:y+h, x:x+w]
            processed_roi = await self._preprocess_printed(roi)
            result[y:y+h, x:x+w] = processed_roi

        for region in handwritten_regions:
            x, y, w, h = region
            roi = gray[y:y+h, x:x+w]
            processed_roi = await self._preprocess_handwritten(roi)
            result[y:y+h, x:x+w] = processed_roi

        return result

    async def _denoise(self, image: np.ndarray) -> np.ndarray:
        """노이즈 제거"""
        # Non-local means 디노이징
        denoised = cv2.fastNlMeansDenoising(image, h=10)

        # 미디언 필터 (솔트앤페퍼 노이즈 제거)
        median = cv2.medianBlur(denoised, 3)

        return median

    async def _deskew(self, image: np.ndarray) -> np.ndarray:
        """이미지 기울기 보정"""
        # 엣지 검출
        edges = cv2.Canny(image, 50, 150, apertureSize=3)

        # 허프 변환으로 직선 검출
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)

        if lines is not None:
            # 각도 계산
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                if -45 <= angle <= 45:
                    angles.append(angle)

            if angles:
                # 중간값 각도 계산
                median_angle = np.median(angles)

                # 회전
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(
                    image, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                return rotated

        return image

    async def _remove_borders(self, image: np.ndarray) -> np.ndarray:
        """문서 테두리 제거"""
        # 이진화
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 컨투어 찾기
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # 가장 큰 컨투어 찾기 (문서 영역)
            largest_contour = max(contours, key=cv2.contourArea)

            # 바운딩 박스
            x, y, w, h = cv2.boundingRect(largest_contour)

            # 여백 추가 (텍스트가 잘리지 않도록)
            margin = 10
            x = max(0, x - margin)
            y = max(0, y - margin)
            w = min(image.shape[1] - x, w + 2 * margin)
            h = min(image.shape[0] - y, h + 2 * margin)

            # 크롭
            cropped = image[y:y+h, x:x+w]
            return cropped

        return image

    async def _binarize(self, image: np.ndarray) -> np.ndarray:
        """이진화 처리"""
        # Otsu's 방법
        _, otsu = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 적응형 임계값
        adaptive = cv2.adaptiveThreshold(
            image, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        # 두 방법 중 더 나은 결과 선택 (텍스트 픽셀 수 기준)
        otsu_text_pixels = np.sum(otsu == 0)
        adaptive_text_pixels = np.sum(adaptive == 0)

        # 적절한 텍스트 픽셀 비율 (5% ~ 30%)
        total_pixels = image.shape[0] * image.shape[1]
        otsu_ratio = otsu_text_pixels / total_pixels
        adaptive_ratio = adaptive_text_pixels / total_pixels

        if 0.05 <= otsu_ratio <= 0.3:
            return otsu
        elif 0.05 <= adaptive_ratio <= 0.3:
            return adaptive
        else:
            # 둘 다 적절하지 않으면 Otsu 사용
            return otsu

    async def _enhance_text(self, image: np.ndarray) -> np.ndarray:
        """텍스트 향상"""
        # 모폴로지 연산
        kernel = np.ones((2, 2), np.uint8)

        # 침식 (텍스트 선명하게)
        eroded = cv2.erode(image, kernel, iterations=1)

        # 팽창 (끊어진 부분 연결)
        dilated = cv2.dilate(eroded, kernel, iterations=1)

        return dilated

    async def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """대비 향상"""
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)

        return enhanced

    async def _sharpen(self, image: np.ndarray) -> np.ndarray:
        """이미지 샤프닝"""
        # 언샤프 마스크
        gaussian = cv2.GaussianBlur(image, (0, 0), 2.0)
        sharpened = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)

        return sharpened

    async def _remove_background(self, image: np.ndarray) -> np.ndarray:
        """배경 제거"""
        # 모폴로지 그래디언트로 배경 추정
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        background = cv2.morphologyEx(image, cv2.MORPH_DILATE, kernel)

        # 배경 제거
        diff = cv2.subtract(background, image)
        normalized = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)

        return normalized

    async def _enhance_pen_strokes(self, image: np.ndarray) -> np.ndarray:
        """펜 자국 향상 (손글씨)"""
        # 가우시안 블러로 부드럽게
        blurred = cv2.GaussianBlur(image, (3, 3), 0)

        # 대비 향상
        enhanced = cv2.convertScaleAbs(blurred, alpha=1.5, beta=0)

        return enhanced

    async def _segment_regions(self, image: np.ndarray) -> Tuple[List, List]:
        """영역 분할 (인쇄/손글씨)"""
        # 텍스트 영역 검출
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 연결된 구성 요소 분석
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

        printed_regions = []
        handwritten_regions = []

        for i in range(1, num_labels):
            x, y, w, h, area = stats[i]

            # 영역 크기와 종횡비로 분류
            aspect_ratio = w / h if h > 0 else 0

            if area > 1000:  # 최소 크기 필터
                # 균일한 크기와 정렬 → 인쇄
                if 0.5 <= aspect_ratio <= 2.0:
                    printed_regions.append((x, y, w, h))
                else:
                    handwritten_regions.append((x, y, w, h))

        return printed_regions, handwritten_regions

    async def detect_text_orientation(self, image: np.ndarray) -> float:
        """텍스트 방향 감지"""
        try:
            # Tesseract OSD (Orientation and Script Detection)
            osd = pytesseract.image_to_osd(image)
            angle = 0

            for line in osd.split('\n'):
                if 'Orientation in degrees' in line:
                    angle = float(line.split(':')[-1].strip())
                    break

            return angle

        except Exception as e:
            logger.error(f"Orientation detection error: {e}")
            return 0

    async def detect_document_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """문서 레이아웃 분석"""
        layout = {
            'columns': [],
            'headers': [],
            'footers': [],
            'paragraphs': [],
            'tables': [],
            'images': []
        }

        # 이진화
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 수평/수직 투영 프로파일
        horizontal_projection = np.sum(binary, axis=1)
        vertical_projection = np.sum(binary, axis=0)

        # 텍스트 라인 검출
        line_threshold = np.mean(horizontal_projection) * 0.5
        text_lines = []
        in_line = False
        start_y = 0

        for y, value in enumerate(horizontal_projection):
            if value > line_threshold and not in_line:
                in_line = True
                start_y = y
            elif value <= line_threshold and in_line:
                in_line = False
                text_lines.append((start_y, y))

        # 컬럼 검출
        column_threshold = np.mean(vertical_projection) * 0.3
        columns = []
        in_column = False
        start_x = 0

        for x, value in enumerate(vertical_projection):
            if value > column_threshold and not in_column:
                in_column = True
                start_x = x
            elif value <= column_threshold and in_column:
                in_column = False
                columns.append((start_x, x))

        layout['text_lines'] = text_lines
        layout['columns'] = columns
        layout['num_columns'] = len(columns)

        return layout