"""
Parsers Module
Handles parsing of various file types: KakaoTalk, Text, PDF, Images, Audio
"""

from .base import BaseParser, Message, StandardMetadata

__all__ = ["BaseParser", "Message", "StandardMetadata"]

# Optional imports - these require additional dependencies
try:
    from .image_ocr import ImageOCRParser
    __all__.append("ImageOCRParser")
except ImportError:
    pass  # pytesseract not installed

try:
    from .image_vision import ImageVisionParser
    __all__.append("ImageVisionParser")
except ImportError:
    pass  # pytesseract or other deps not installed

try:
    from .pdf_parser import PDFParser
    __all__.append("PDFParser")
except ImportError:
    pass  # PyPDF2 not installed

try:
    from .audio_parser import AudioParser
    __all__.append("AudioParser")
except ImportError:
    pass  # openai not installed

try:
    from .video_parser import VideoParser
    __all__.append("VideoParser")
except ImportError:
    pass  # ffmpeg-python not installed
