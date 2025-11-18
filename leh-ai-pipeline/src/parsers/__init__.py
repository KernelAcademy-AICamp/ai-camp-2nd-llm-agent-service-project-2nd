"""
Parsers Module
Handles parsing of various file types: KakaoTalk, Text, PDF, Images
"""

from .base import BaseParser, Message
from .image_ocr import ImageOCRParser

__all__ = ["BaseParser", "Message", "ImageOCRParser"]
