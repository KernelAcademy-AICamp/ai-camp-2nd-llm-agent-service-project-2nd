"""
Parsers Module
Handles parsing of various file types: KakaoTalk, Text, PDF, Images, Audio
"""

from .base import BaseParser, Message
from .image_ocr import ImageOCRParser
from .image_vision import ImageVisionParser
from .pdf_parser import PDFParser
from .audio_parser import AudioParser
from .video_parser import VideoParser

# V2 Parsers - Enhanced versions with legal citation support
from .kakaotalk_v2 import KakaoTalkParserV2, ParsedMessage as KakaoTalkMessage, ParsingResult as KakaoTalkParsingResult
from .pdf_parser_v2 import PDFParserV2, ParsedPage, PDFParsingResult
from .audio_parser_v2 import AudioParserV2, AudioSegment, AudioMetadata, AudioParsingResult
from .image_parser_v2 import (
    ImageParserV2, ParsedImage, ImageParsingResult,
    GPSCoordinates, DeviceInfo, EXIFMetadata
)

__all__ = [
    # V1 Parsers
    "BaseParser", "Message",
    "ImageOCRParser", "ImageVisionParser",
    "PDFParser", "AudioParser", "VideoParser",
    # V2 Parsers
    "KakaoTalkParserV2", "KakaoTalkMessage", "KakaoTalkParsingResult",
    "PDFParserV2", "ParsedPage", "PDFParsingResult",
    "AudioParserV2", "AudioSegment", "AudioMetadata", "AudioParsingResult",
    "ImageParserV2", "ParsedImage", "ImageParsingResult",
    "GPSCoordinates", "DeviceInfo", "EXIFMetadata",
]
