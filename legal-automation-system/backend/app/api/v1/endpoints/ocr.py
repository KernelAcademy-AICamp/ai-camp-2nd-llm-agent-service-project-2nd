"""
OCR API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
import tempfile
import os

from app.database.session import get_db
from app.services.ocr.document_parser import DocumentParser, OCRProcessor
from app.services.ocr.pdf_processor import PDFProcessor
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/process")
async def process_document_ocr(
    file: UploadFile = File(...),
    extract_metadata: bool = Query(True),
    extract_structure: bool = Query(True),
    ocr_engine: str = Query("auto", regex="^(auto|tesseract|easyocr)$"),
    current_user: User = Depends(get_current_user)
):
    """
    문서 OCR 처리

    지원 파일 형식:
    - PDF
    - 이미지 (JPG, PNG, TIFF)
    - DOCX
    - TXT
    """
    # 파일 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        parser = DocumentParser()

        # OCR 처리
        result = await parser.parse_document(
            file_path=tmp_file_path,
            extract_metadata=extract_metadata,
            extract_structure=extract_structure
        )

        return {
            "filename": file.filename,
            "text": result['text'],
            "metadata": result.get('metadata', {}) if extract_metadata else None,
            "structure": result.get('structure', {}) if extract_structure else None,
            "document_type": result.get('document_type', 'unknown'),
            "hash": result.get('hash', '')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@router.post("/pdf/extract")
async def extract_pdf_text(
    file: UploadFile = File(...),
    method: str = Query("auto", regex="^(auto|pdfplumber|pypdf2|pymupdf|ocr)$"),
    extract_tables: bool = Query(False),
    extract_images: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """
    PDF 텍스트 추출

    추출 방법:
    - auto: 자동 선택
    - pdfplumber: 구조화된 텍스트 추출
    - pypdf2: 기본 텍스트 추출
    - pymupdf: 고급 렌더링
    - ocr: OCR 기반 추출
    """
    # 파일 확인
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # 파일 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        pdf_processor = PDFProcessor()

        # PDF 처리
        result = await pdf_processor.extract_text(
            file_path=tmp_file_path,
            method=method,
            ocr_fallback=True
        )

        response = {
            "filename": file.filename,
            "text": result['text'],
            "total_pages": result.get('total_pages', 0),
            "method_used": result.get('method', 'unknown')
        }

        # 테이블 추출
        if extract_tables and result.get('tables'):
            response['tables'] = result['tables']

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@router.post("/image/ocr")
async def process_image_ocr(
    file: UploadFile = File(...),
    engine: str = Query("auto", regex="^(auto|tesseract|easyocr)$"),
    preprocess: bool = Query(True),
    current_user: User = Depends(get_current_user)
):
    """
    이미지 OCR 처리
    """
    # 파일 확인
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="Unsupported image format")

    # 파일 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        import cv2
        import numpy as np

        # 이미지 로드
        image = cv2.imread(tmp_file_path)
        if image is None:
            raise HTTPException(status_code=400, detail="Failed to load image")

        ocr_processor = OCRProcessor()

        # OCR 처리
        result = await ocr_processor.process_image(image, engine=engine)

        return {
            "filename": file.filename,
            "text": result['text'],
            "confidence": result.get('confidence', 0),
            "engine_used": result.get('engine', 'unknown')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@router.post("/legal-sections")
async def extract_legal_sections(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    법률 문서의 조항 추출

    법률 문서에서 조항, 항, 호, 목을 구조화하여 추출합니다.
    """
    # 파일 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        if file.filename.lower().endswith('.pdf'):
            pdf_processor = PDFProcessor()
            sections = await pdf_processor.extract_legal_sections(tmp_file_path)
        else:
            # 다른 형식은 일반 파서 사용
            parser = DocumentParser()
            result = await parser.parse_document(tmp_file_path)
            sections = result.get('structure', {})

        return {
            "filename": file.filename,
            "sections": sections
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)