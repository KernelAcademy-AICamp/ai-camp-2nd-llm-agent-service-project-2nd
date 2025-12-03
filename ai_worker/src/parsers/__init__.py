"""
Parsers Module
Handles parsing of various file types: KakaoTalk, Text, PDF, Images, Audio
"""

from .base import BaseParser, Message, StandardMetadata

__all__ = ["BaseParser", "Message", "StandardMetadata"]

# Optional imports - these require additional dependencies
# noqa: F401 comments are used because these are re-exports for the public API
try:
    from .image_ocr import ImageOCRParser  # noqa: F401
    __all__.append("ImageOCRParser")
except ImportError:
    pass  # pytesseract not installed

try:
    from .image_vision import ImageVisionParser  # noqa: F401
    __all__.append("ImageVisionParser")
except ImportError:
    pass  # pytesseract or other deps not installed

try:
    from .pdf_parser import PDFParser  # noqa: F401
    __all__.append("PDFParser")
except ImportError:
    pass  # PyPDF2 not installed

try:
    from .audio_parser import AudioParser  # noqa: F401
    __all__.append("AudioParser")
except ImportError:
    pass  # openai not installed

try:
    from .video_parser import VideoParser  # noqa: F401
    __all__.append("VideoParser")
except ImportError:
    pass  # ffmpeg-python not installed

# V2 Parsers - Enhanced versions with legal citation support
try:
    from .kakaotalk_v2 import (  # noqa: F401
        KakaoTalkParserV2,
        ParsedMessage as KakaoTalkMessage,
        ParsingResult as KakaoTalkParsingResult
    )
    __all__.extend(["KakaoTalkParserV2", "KakaoTalkMessage", "KakaoTalkParsingResult"])
except ImportError:
    pass

try:
    from .pdf_parser_v2 import PDFParserV2, ParsedPage, PDFParsingResult  # noqa: F401
    __all__.extend(["PDFParserV2", "ParsedPage", "PDFParsingResult"])
except ImportError:
    pass

try:
    from .audio_parser_v2 import (  # noqa: F401
        AudioParserV2, AudioSegment, AudioMetadata, AudioParsingResult
    )
    __all__.extend(["AudioParserV2", "AudioSegment", "AudioMetadata", "AudioParsingResult"])
except ImportError:
    pass

try:
    from .image_parser_v2 import (  # noqa: F401
        ImageParserV2, ParsedImage, ImageParsingResult,
        GPSCoordinates, DeviceInfo, EXIFMetadata
    )
    __all__.extend([
        "ImageParserV2", "ParsedImage", "ImageParsingResult",
        "GPSCoordinates", "DeviceInfo", "EXIFMetadata"
    ])
except ImportError:
    pass
