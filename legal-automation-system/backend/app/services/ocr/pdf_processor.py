"""
PDF 문서 전문 처리 모듈
"""

import io
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import asyncio

import pdfplumber
import PyPDF2
from pdf2image import convert_from_path, convert_from_bytes
import fitz  # PyMuPDF
import numpy as np
from PIL import Image

from app.core.logging import logger


class PDFProcessor:
    """PDF 문서 특화 처리기"""

    def __init__(self):
        """PDF 프로세서 초기화"""
        self.extraction_methods = [
            'pdfplumber',  # 구조화된 텍스트
            'pypdf2',      # 기본 텍스트
            'pymupdf',     # 고급 렌더링
            'ocr'          # 이미지 기반
        ]

    async def extract_text(
        self,
        file_path: str,
        method: str = "auto",
        ocr_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        PDF에서 텍스트 추출

        Args:
            file_path: PDF 파일 경로
            method: 추출 방법
            ocr_fallback: OCR 폴백 사용 여부

        Returns:
            추출된 텍스트 및 메타데이터
        """
        file_path = Path(file_path)

        if method == "auto":
            # 자동으로 최적 방법 선택
            return await self._extract_auto(file_path, ocr_fallback)

        # 특정 방법으로 추출
        extractors = {
            'pdfplumber': self._extract_pdfplumber,
            'pypdf2': self._extract_pypdf2,
            'pymupdf': self._extract_pymupdf,
            'ocr': self._extract_ocr
        }

        if method in extractors:
            return await extractors[method](file_path)
        else:
            raise ValueError(f"Unknown extraction method: {method}")

    async def _extract_auto(self, file_path: Path, ocr_fallback: bool) -> Dict[str, Any]:
        """자동으로 최적 추출 방법 선택"""
        # 1. 먼저 텍스트 기반 추출 시도
        result = await self._extract_pdfplumber(file_path)

        # 텍스트가 충분히 추출되었는지 확인
        if result['text'] and len(result['text'].strip()) > 100:
            return result

        # 2. PyMuPDF로 시도
        result = await self._extract_pymupdf(file_path)
        if result['text'] and len(result['text'].strip()) > 100:
            return result

        # 3. OCR 폴백
        if ocr_fallback:
            logger.info("Text extraction failed, falling back to OCR")
            return await self._extract_ocr(file_path)

        return result

    async def _extract_pdfplumber(self, file_path: Path) -> Dict[str, Any]:
        """pdfplumber를 사용한 텍스트 추출"""
        try:
            text_pages = []
            tables_all = []
            metadata = {}

            with pdfplumber.open(file_path) as pdf:
                # 메타데이터 추출
                metadata = pdf.metadata or {}

                for i, page in enumerate(pdf.pages):
                    # 페이지 텍스트 추출
                    page_text = page.extract_text() or ''

                    # 테이블 추출
                    tables = page.extract_tables() or []

                    text_pages.append({
                        'page': i + 1,
                        'text': page_text,
                        'tables': tables,
                        'bbox': page.bbox
                    })

                    if tables:
                        tables_all.extend(tables)

            # 전체 텍스트 결합
            full_text = '\n\n'.join([p['text'] for p in text_pages if p['text']])

            return {
                'text': full_text,
                'pages': text_pages,
                'tables': tables_all,
                'metadata': metadata,
                'method': 'pdfplumber',
                'total_pages': len(text_pages)
            }

        except Exception as e:
            logger.error(f"pdfplumber extraction error: {e}")
            return {'text': '', 'error': str(e), 'method': 'pdfplumber'}

    async def _extract_pypdf2(self, file_path: Path) -> Dict[str, Any]:
        """PyPDF2를 사용한 텍스트 추출"""
        try:
            text_pages = []

            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                # 메타데이터 추출
                metadata = pdf_reader.metadata if pdf_reader.metadata else {}

                for i in range(num_pages):
                    page = pdf_reader.pages[i]
                    text = page.extract_text()

                    text_pages.append({
                        'page': i + 1,
                        'text': text
                    })

            # 전체 텍스트 결합
            full_text = '\n\n'.join([p['text'] for p in text_pages if p['text']])

            return {
                'text': full_text,
                'pages': text_pages,
                'metadata': metadata,
                'method': 'pypdf2',
                'total_pages': num_pages
            }

        except Exception as e:
            logger.error(f"PyPDF2 extraction error: {e}")
            return {'text': '', 'error': str(e), 'method': 'pypdf2'}

    async def _extract_pymupdf(self, file_path: Path) -> Dict[str, Any]:
        """PyMuPDF를 사용한 텍스트 추출"""
        try:
            doc = fitz.open(file_path)
            text_pages = []
            annotations_all = []

            for i, page in enumerate(doc):
                # 텍스트 추출
                text = page.get_text()

                # 주석 추출
                annotations = []
                for annot in page.annots():
                    annotations.append({
                        'type': annot.type[1],
                        'content': annot.info.get('content', ''),
                        'author': annot.info.get('title', ''),
                        'page': i + 1
                    })

                text_pages.append({
                    'page': i + 1,
                    'text': text,
                    'annotations': annotations
                })

                annotations_all.extend(annotations)

            # 메타데이터 추출
            metadata = doc.metadata

            # 전체 텍스트 결합
            full_text = '\n\n'.join([p['text'] for p in text_pages if p['text']])

            doc.close()

            return {
                'text': full_text,
                'pages': text_pages,
                'annotations': annotations_all,
                'metadata': metadata,
                'method': 'pymupdf',
                'total_pages': len(text_pages)
            }

        except Exception as e:
            logger.error(f"PyMuPDF extraction error: {e}")
            return {'text': '', 'error': str(e), 'method': 'pymupdf'}

    async def _extract_ocr(self, file_path: Path) -> Dict[str, Any]:
        """OCR을 사용한 텍스트 추출"""
        from .document_parser import OCRProcessor

        try:
            ocr = OCRProcessor()
            text_pages = []

            # PDF를 이미지로 변환
            images = convert_from_path(str(file_path), dpi=300)

            # 각 페이지 OCR 처리
            for i, image in enumerate(images):
                # PIL Image를 numpy 배열로 변환
                img_array = np.array(image)

                # OCR 수행
                result = await ocr.process_image(img_array)

                text_pages.append({
                    'page': i + 1,
                    'text': result['text'],
                    'confidence': result.get('confidence', 0),
                    'method': 'ocr'
                })

            # 전체 텍스트 결합
            full_text = '\n\n'.join([p['text'] for p in text_pages if p['text']])

            return {
                'text': full_text,
                'pages': text_pages,
                'method': 'ocr',
                'total_pages': len(text_pages)
            }

        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return {'text': '', 'error': str(e), 'method': 'ocr'}

    async def extract_forms(self, file_path: str) -> Dict[str, Any]:
        """PDF 폼 필드 추출"""
        try:
            doc = fitz.open(file_path)
            forms = []

            for page_num, page in enumerate(doc):
                widgets = page.widgets()
                for widget in widgets:
                    field_info = {
                        'page': page_num + 1,
                        'field_name': widget.field_name,
                        'field_type': widget.field_type_string,
                        'field_value': widget.field_value,
                        'rect': list(widget.rect),
                        'flags': widget.field_flags
                    }
                    forms.append(field_info)

            doc.close()

            return {
                'forms': forms,
                'total_fields': len(forms)
            }

        except Exception as e:
            logger.error(f"Form extraction error: {e}")
            return {'forms': [], 'error': str(e)}

    async def extract_images(self, file_path: str, output_dir: str = None) -> List[Dict[str, Any]]:
        """PDF에서 이미지 추출"""
        try:
            doc = fitz.open(file_path)
            images = []
            output_path = Path(output_dir) if output_dir else None

            if output_path:
                output_path.mkdir(parents=True, exist_ok=True)

            for page_num, page in enumerate(doc):
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    # 이미지 데이터 추출
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)

                    img_data = {
                        'page': page_num + 1,
                        'index': img_index,
                        'width': pix.width,
                        'height': pix.height,
                        'colorspace': pix.colorspace.name,
                        'xref': xref
                    }

                    # 이미지 저장 (선택적)
                    if output_path:
                        img_path = output_path / f"page{page_num + 1}_img{img_index}.png"
                        pix.save(str(img_path))
                        img_data['saved_path'] = str(img_path)

                    images.append(img_data)
                    pix = None

            doc.close()

            return images

        except Exception as e:
            logger.error(f"Image extraction error: {e}")
            return []

    async def split_pdf(self, file_path: str, output_dir: str, pages_per_file: int = 1) -> List[str]:
        """PDF 분할"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            output_files = []

            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)

                for start_page in range(0, total_pages, pages_per_file):
                    pdf_writer = PyPDF2.PdfWriter()
                    end_page = min(start_page + pages_per_file, total_pages)

                    for page_num in range(start_page, end_page):
                        pdf_writer.add_page(pdf_reader.pages[page_num])

                    # 출력 파일 저장
                    output_file = output_path / f"pages_{start_page + 1}_to_{end_page}.pdf"
                    with open(output_file, 'wb') as output:
                        pdf_writer.write(output)

                    output_files.append(str(output_file))

            return output_files

        except Exception as e:
            logger.error(f"PDF split error: {e}")
            return []

    async def merge_pdfs(self, pdf_files: List[str], output_path: str) -> bool:
        """여러 PDF 파일 병합"""
        try:
            pdf_merger = PyPDF2.PdfMerger()

            for pdf_file in pdf_files:
                pdf_merger.append(pdf_file)

            with open(output_path, 'wb') as output:
                pdf_merger.write(output)

            pdf_merger.close()
            return True

        except Exception as e:
            logger.error(f"PDF merge error: {e}")
            return False

    async def add_watermark(self, input_path: str, watermark_path: str, output_path: str) -> bool:
        """PDF에 워터마크 추가"""
        try:
            # 원본 PDF 열기
            pdf_reader = PyPDF2.PdfReader(input_path)
            pdf_writer = PyPDF2.PdfWriter()

            # 워터마크 PDF 열기
            watermark_reader = PyPDF2.PdfReader(watermark_path)
            watermark_page = watermark_reader.pages[0]

            # 각 페이지에 워터마크 추가
            for page in pdf_reader.pages:
                page.merge_page(watermark_page)
                pdf_writer.add_page(page)

            # 결과 저장
            with open(output_path, 'wb') as output:
                pdf_writer.write(output)

            return True

        except Exception as e:
            logger.error(f"Watermark error: {e}")
            return False

    async def extract_legal_sections(self, file_path: str) -> Dict[str, Any]:
        """법률 문서의 조항 추출"""
        # 텍스트 추출
        result = await self.extract_text(file_path)
        text = result.get('text', '')

        sections = {
            'articles': [],     # 조항
            'paragraphs': [],   # 항
            'items': [],        # 호
            'subitems': []      # 목
        }

        # 조항 패턴 (제1조, 제2조 등)
        article_pattern = r'제(\d+)조\s*[\(（]([^)）]+)[\)）]([^제]*?)(?=제\d+조|$)'
        articles = re.finditer(article_pattern, text, re.DOTALL)

        for match in articles:
            article = {
                'number': int(match.group(1)),
                'title': match.group(2).strip(),
                'content': match.group(3).strip(),
                'start_pos': match.start(),
                'end_pos': match.end()
            }

            # 항 찾기 (①, ②, ③ 등)
            paragraph_pattern = r'[①②③④⑤⑥⑦⑧⑨⑩]\s*([^①②③④⑤⑥⑦⑧⑨⑩]*)'
            paragraphs = re.finditer(paragraph_pattern, article['content'])

            article['paragraphs'] = []
            for para_match in paragraphs:
                article['paragraphs'].append(para_match.group(1).strip())

            sections['articles'].append(article)

        return sections