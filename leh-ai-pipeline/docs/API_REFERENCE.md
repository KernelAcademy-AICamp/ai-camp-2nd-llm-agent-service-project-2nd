# LEH AI Pipeline - API Reference

모든 클래스 및 메서드의 상세 API 레퍼런스

---

## 목차

- [Parsers](#parsers)
- [Analysis](#analysis)
- [Storage](#storage)
- [Search](#search)
- [Data Models](#data-models)

---

## Parsers

### BaseParser (Abstract)

모든 파서의 기본 인터페이스

```python
from src.parsers.base import BaseParser, Message

class BaseParser(ABC):
    """파일 파서의 추상 기본 클래스"""

    @abstractmethod
    def parse(self, file_path: str) -> List[Message]:
        """
        파일을 파싱하여 메시지 리스트로 변환

        Args:
            file_path (str): 파싱할 파일의 절대 경로

        Returns:
            List[Message]: 파싱된 메시지 리스트

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            Exception: 파싱 실패 시
        """
        pass
```

### KakaoTalkParser

카카오톡 대화 파일 파서

```python
from src.parsers.kakaotalk import KakaoTalkParser

parser = KakaoTalkParser()
messages = parser.parse("kakao_chat.txt")
```

**메서드**:

```python
def parse(self, file_path: str) -> List[Message]:
    """
    카카오톡 대화 파일 파싱

    Args:
        file_path (str): 카카오톡 대화 파일 (.txt)

    Returns:
        List[Message]: 파싱된 메시지
        - content: 메시지 내용
        - sender: 발신자 이름
        - timestamp: 발신 시간 (YYYY-MM-DD HH:MM 형식 파싱)

    Example:
        >>> parser = KakaoTalkParser()
        >>> messages = parser.parse("chat.txt")
        >>> print(messages[0].content)
        "안녕하세요"
    """
```

### PDFParser

PDF 문서 파서

```python
from src.parsers.pdf_parser import PDFParser

parser = PDFParser()
messages = parser.parse("document.pdf")
```

**메서드**:

```python
def parse(self, file_path: str) -> List[Message]:
    """
    PDF 문서를 페이지별로 파싱

    Args:
        file_path (str): PDF 파일 경로

    Returns:
        List[Message]: 페이지별 메시지
        - content: 페이지 텍스트
        - sender: "Document"
        - timestamp: 파싱 시간

    Note:
        PyPDF2 라이브러리 사용
        이미지 내 텍스트는 추출되지 않음 (ImageOCRParser 사용)
    """
```

### AudioParser

오디오 파일 STT 파서

```python
from src.parsers.audio_parser import AudioParser

parser = AudioParser()
messages = parser.parse(
    file_path="audio.mp3",
    default_sender="Speaker",
    base_timestamp=datetime.now()
)
```

**메서드**:

```python
def parse(
    self,
    file_path: str,
    default_sender: str = "Speaker",
    base_timestamp: Optional[datetime] = None
) -> List[Message]:
    """
    오디오 파일을 Whisper STT로 변환

    Args:
        file_path (str): 오디오 파일 경로 (.mp3, .m4a, .wav)
        default_sender (str): 발신자 이름 (기본값: "Speaker")
        base_timestamp (datetime, optional): 기준 시간 (기본값: 현재 시간)

    Returns:
        List[Message]: 세그먼트별 메시지
        - content: 음성 인식 텍스트
        - sender: default_sender
        - timestamp: base_timestamp + segment 시작 시간

    Example:
        >>> parser = AudioParser()
        >>> messages = parser.parse("call_record.mp3")
        >>> for msg in messages:
        ...     print(f"[{msg.timestamp}] {msg.content}")
    """
```

### VideoParser

비디오 파일 파서 (오디오 추출 + STT)

```python
from src.parsers.video_parser import VideoParser

parser = VideoParser()
messages = parser.parse("video.mp4")
```

**메서드**:

```python
def parse(
    self,
    file_path: str,
    default_sender: str = "Speaker",
    base_timestamp: Optional[datetime] = None
) -> List[Message]:
    """
    비디오 → 오디오 → 텍스트 변환

    Args:
        file_path (str): 비디오 파일 경로 (.mp4, .avi, .mov)
        default_sender (str): 발신자 이름
        base_timestamp (datetime, optional): 기준 시간

    Returns:
        List[Message]: 음성 인식 결과

    Process:
        1. ffmpeg으로 오디오 추출 (mp3, 16kHz, mono)
        2. 임시 파일로 저장
        3. AudioParser로 STT
        4. 임시 파일 자동 삭제

    Raises:
        Exception: ffmpeg 실패 시
    """
```

### ImageOCRParser

이미지 OCR 파서

```python
from src.parsers.image_ocr import ImageOCRParser

parser = ImageOCRParser()
messages = parser.parse("screenshot.jpg")
```

**메서드**:

```python
def parse(self, file_path: str) -> List[Message]:
    """
    이미지에서 텍스트 추출 (Tesseract OCR)

    Args:
        file_path (str): 이미지 파일 경로

    Returns:
        List[Message]: OCR 결과
        - content: 인식된 텍스트
        - sender: "OCR"
        - timestamp: 파싱 시간

    Note:
        한국어 + 영어 동시 인식 (lang='kor+eng')
        빈 텍스트는 필터링됨
    """
```

### ImageVisionParser

이미지 감정/맥락 분석 파서 (GPT-4o Vision)

```python
from src.parsers.image_vision import ImageVisionParser, VisionAnalysis

parser = ImageVisionParser()
analysis = parser.analyze_vision("photo.jpg")
messages = parser.parse("photo.jpg")  # OCR + Vision 통합
```

**메서드**:

```python
def analyze_vision(self, file_path: str) -> VisionAnalysis:
    """
    이미지 감정, 맥락, 분위기 분석

    Args:
        file_path (str): 이미지 파일 경로

    Returns:
        VisionAnalysis:
            - emotions (List[str]): 감지된 감정 ["happy", "sad", ...]
            - context (str): 이미지 맥락 설명
            - atmosphere (str): 전체 분위기
            - confidence (float): 분석 신뢰도 (0.0-1.0)

    Example:
        >>> parser = ImageVisionParser()
        >>> result = parser.analyze_vision("wedding.jpg")
        >>> print(result.emotions)
        ["happy", "joyful"]
        >>> print(result.context)
        "결혼식 장면으로 보임"
    """

def parse(self, file_path: str) -> List[Message]:
    """
    OCR + Vision 통합 파싱

    Returns:
        List[Message]: [OCR 결과, Vision 분석 결과]
    """
```

---

## Analysis

### EvidenceScorer

증거 가치 점수 산정

```python
from src.analysis.evidence_scorer import EvidenceScorer, ScoringResult

scorer = EvidenceScorer()
result = scorer.score(message)
```

**메서드**:

```python
def score(self, message: Message) -> ScoringResult:
    """
    단일 메시지 점수 산정

    Args:
        message (Message): 평가할 메시지

    Returns:
        ScoringResult:
            - score (float): 0-10점 증거 점수
            - matched_keywords (List[str]): 매칭된 키워드
            - categories (List[str]): 관련 카테고리

    Scoring Logic:
        - 기본 점수: 0.5
        - 카테고리별 가중치:
            divorce: 3.0
            violence: 3.5
            financial: 2.5
            affair: 3.0
            abuse: 3.0
        - 다중 키워드 매칭 시 가산점
        - 최종 점수 0-10 범위로 정규화
    """

def score_batch(self, messages: List[Message]) -> List[ScoringResult]:
    """여러 메시지 일괄 점수 산정"""
```

### RiskAnalyzer

사건 위험도 분석

```python
from src.analysis.risk_analyzer import RiskAnalyzer, RiskAnalysis, RiskLevel

analyzer = RiskAnalyzer()
risk = analyzer.analyze(messages)
```

**메서드**:

```python
def analyze(self, messages: List[Message]) -> RiskAnalysis:
    """
    위험도 종합 분석

    Args:
        messages (List[Message]): 분석할 메시지 목록

    Returns:
        RiskAnalysis:
            - violence_risk (RiskLevel): 폭력 위험도
            - financial_risk (RiskLevel): 금전 분쟁 위험도
            - custody_risk (RiskLevel): 양육권 분쟁 위험도
            - overall_risk (RiskLevel): 종합 위험도
            - risk_indicators (List[str]): 위험 지표 목록

    RiskLevel: low | medium | high | critical

    Example:
        >>> risk = analyzer.analyze(messages)
        >>> if risk.violence_risk == RiskLevel.CRITICAL:
        ...     print("긴급 개입 필요")
    """
```

### Article840Tagger

민법 840조 이혼 사유 태깅

```python
from src.analysis.article_840_tagger import Article840Tagger, Article840Category

tagger = Article840Tagger()
result = tagger.tag(message)
```

**메서드**:

```python
def tag(self, message: Message) -> TaggingResult:
    """
    민법 840조 카테고리 자동 분류

    Args:
        message (Message): 분류할 메시지

    Returns:
        TaggingResult:
            - categories (List[Article840Category]): 분류된 카테고리 (복수 가능)
            - confidence (float): 분류 신뢰도 (0.0-1.0)
            - matched_keywords (Dict[Article840Category, List[str]]): 카테고리별 매칭 키워드

    Categories:
        - ADULTERY: 배우자 부정행위
        - DESERTION: 악의의 유기
        - MISTREATMENT_BY_INLAWS: 배우자 직계존속의 부당한 대우
        - HARM_TO_OWN_PARENTS: 자기 직계존속 학대/유기
        - UNKNOWN_WHEREABOUTS: 생사 3년 불명
        - IRRECONCILABLE_DIFFERENCES: 혼인 지속 불가 중대 사유
        - GENERAL: 일반 증거

    Example:
        >>> result = tagger.tag(message)
        >>> if Article840Category.ADULTERY in result.categories:
        ...     print(f"외도 관련 증거 (신뢰도: {result.confidence})")
    """

def tag_batch(self, messages: List[Message]) -> List[TaggingResult]:
    """여러 메시지 일괄 태깅"""
```

### EvidenceSummarizer

LLM 기반 증거 요약

```python
from src.analysis.summarizer import EvidenceSummarizer, SummaryType

summarizer = EvidenceSummarizer(model="gpt-4o")
summary = summarizer.summarize_conversation(messages)
```

**메서드**:

```python
def summarize_conversation(
    self,
    messages: List[Message],
    max_words: Optional[int] = None,
    language: str = "ko"
) -> SummaryResult:
    """
    대화 요약

    Args:
        messages (List[Message]): 요약할 대화 메시지
        max_words (int, optional): 최대 단어 수
        language (str): 요약 언어 ("ko" or "en")

    Returns:
        SummaryResult:
            - summary (str): 요약문
            - summary_type (SummaryType): CONVERSATION
            - key_points (List[str]): 핵심 포인트 (3-5개)
            - word_count (int): 단어 수

    Example:
        >>> summary = summarizer.summarize_conversation(messages, max_words=100)
        >>> print(summary.summary)
        "외도 관련 대화로, 배우자의 부정행위 증거가 포함됨"
        >>> print(summary.key_points)
        ["외도 사실 인정", "증거 사진 언급", "이혼 협의 요구"]
    """

def summarize_document(
    self,
    text: str,
    max_words: Optional[int] = None,
    language: str = "ko"
) -> SummaryResult:
    """
    문서 요약

    Args:
        text (str): 요약할 문서 텍스트
        max_words (int, optional): 최대 단어 수
        language (str): 요약 언어

    Returns:
        SummaryResult (summary_type=DOCUMENT)
    """

def summarize_evidence(
    self,
    messages: List[Message],
    max_words: Optional[int] = None,
    language: str = "ko"
) -> SummaryResult:
    """
    증거 컬렉션 요약

    Args:
        messages (List[Message]): 증거 메시지 목록
        max_words (int, optional): 최대 단어 수
        language (str): 요약 언어

    Returns:
        SummaryResult (summary_type=EVIDENCE)

    Note:
        대화 요약과 달리 증거의 법적 의미에 초점
    """
```

### AnalysisEngine

통합 분석 엔진

```python
from src.analysis.analysis_engine import AnalysisEngine, AnalysisResult

engine = AnalysisEngine()
result = engine.analyze(messages)
```

**메서드**:

```python
def analyze(self, messages: List[Message]) -> AnalysisResult:
    """
    종합 분석 수행

    Args:
        messages (List[Message]): 분석할 메시지

    Returns:
        AnalysisResult:
            - scored_messages (List[Tuple[Message, ScoringResult]]): 점수화된 메시지
            - risk_analysis (RiskAnalysis): 위험도 분석
            - summary (Dict): 통계 요약
                - total_messages (int)
                - average_score (float)
                - high_value_count (int)
                - risk_level (str)

    Example:
        >>> result = engine.analyze(messages)
        >>> print(f"평균 점수: {result.summary['average_score']}")
        >>> print(f"위험도: {result.risk_analysis.overall_risk}")
    """

def get_high_value_messages(
    self,
    messages: List[Message],
    threshold: float = 7.0
) -> List[Tuple[Message, ScoringResult]]:
    """
    고가치 증거 추출

    Args:
        messages (List[Message]): 메시지 목록
        threshold (float): 점수 임계값 (기본 7.0)

    Returns:
        List[Tuple[Message, ScoringResult]]: 임계값 이상 메시지
    """
```

---

## Storage

### MetadataStore

SQLite 메타데이터 저장소

```python
from src.storage.metadata_store import MetadataStore
from src.storage.schemas import EvidenceFile, EvidenceChunk

store = MetadataStore(db_path="./data/metadata.db")
```

**파일 관리 메서드**:

```python
def save_file(self, file: EvidenceFile) -> None:
    """파일 메타데이터 저장"""

def get_file(self, file_id: str) -> Optional[EvidenceFile]:
    """파일 조회"""

def get_files_by_case(self, case_id: str) -> List[EvidenceFile]:
    """케이스별 파일 목록"""

def delete_file(self, file_id: str) -> None:
    """파일 삭제"""
```

**청크 관리 메서드**:

```python
def save_chunk(self, chunk: EvidenceChunk) -> None:
    """청크 메타데이터 저장"""

def save_chunks(self, chunks: List[EvidenceChunk]) -> None:
    """여러 청크 일괄 저장"""

def get_chunk(self, chunk_id: str) -> Optional[EvidenceChunk]:
    """청크 조회"""

def get_chunks_by_file(self, file_id: str) -> List[EvidenceChunk]:
    """파일별 청크 목록"""

def get_chunks_by_case(self, case_id: str) -> List[EvidenceChunk]:
    """케이스별 청크 목록"""

def update_chunk_score(self, chunk_id: str, score: float) -> None:
    """청크 점수 업데이트"""

def delete_chunk(self, chunk_id: str) -> None:
    """청크 삭제"""
```

**케이스 관리 메서드**:

```python
def list_cases(self) -> List[str]:
    """
    전체 케이스 ID 목록

    Returns:
        List[str]: 케이스 ID 목록 (중복 제거, 정렬)
    """

def list_cases_with_stats(self) -> List[Dict[str, Any]]:
    """
    케이스별 통계 포함 목록

    Returns:
        List[Dict]:
            - case_id (str)
            - file_count (int)
            - chunk_count (int)
    """

def get_case_stats(self, case_id: str) -> Dict[str, Any]:
    """
    특정 케이스 통계

    Args:
        case_id (str): 케이스 ID

    Returns:
        Dict:
            - case_id (str)
            - file_count (int)
            - chunk_count (int)
    """

def delete_case(self, case_id: str) -> None:
    """
    케이스 메타데이터 삭제 (벡터는 유지)

    Args:
        case_id (str): 삭제할 케이스 ID

    Note:
        - evidence_chunks WHERE case_id = ? 삭제
        - evidence_files WHERE case_id = ? 삭제
        - 벡터는 삭제하지 않음 (delete_case_complete 사용)
    """

def delete_case_complete(self, case_id: str, vector_store) -> None:
    """
    케이스 완전 삭제 (메타데이터 + 벡터)

    Args:
        case_id (str): 삭제할 케이스 ID
        vector_store (VectorStore): 벡터 저장소 인스턴스

    Process:
        1. 청크의 vector_id 목록 추출
        2. VectorStore에서 벡터 삭제
        3. 메타데이터 삭제
    """
```

**통계 메서드**:

```python
def count_files_by_case(self, case_id: str) -> int:
    """케이스별 파일 개수"""

def count_chunks_by_case(self, case_id: str) -> int:
    """케이스별 청크 개수"""
```

### VectorStore

ChromaDB 벡터 저장소

```python
from src.storage.vector_store import VectorStore

store = VectorStore(persist_directory="./data/chromadb")
```

**벡터 관리 메서드**:

```python
def add_evidence(
    self,
    text: str,
    embedding: List[float],
    metadata: Dict[str, Any]
) -> str:
    """
    단일 벡터 추가

    Args:
        text (str): 원본 텍스트
        embedding (List[float]): 768차원 임베딩 벡터
        metadata (Dict): 메타데이터 (반드시 case_id 포함)

    Returns:
        str: 생성된 vector_id (UUID)
    """

def add_evidences(
    self,
    texts: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]]
) -> List[str]:
    """여러 벡터 일괄 추가"""

def search(
    self,
    query_embedding: List[float],
    n_results: int = 10,
    where: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    벡터 유사도 검색

    Args:
        query_embedding (List[float]): 쿼리 임베딩
        n_results (int): 반환 결과 개수
        where (Dict, optional): 메타데이터 필터
            예: {"case_id": "case_001"}

    Returns:
        List[Dict]:
            - id (str): 벡터 ID
            - distance (float): 유사도 거리 (낮을수록 유사)
            - metadata (Dict): 메타데이터
            - document (str): 원본 텍스트

    Example:
        >>> results = store.search(
        ...     query_embedding=embedding,
        ...     n_results=5,
        ...     where={"case_id": "case_001"}
        ... )
    """

def get_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
    """ID로 벡터 조회"""

def delete_by_id(self, vector_id: str) -> None:
    """ID로 벡터 삭제"""

def count() -> int:
    """전체 벡터 개수"""

def clear() -> None:
    """모든 벡터 삭제"""
```

**케이스 격리 메서드**:

```python
def count_by_case(self, case_id: str) -> int:
    """
    케이스별 벡터 개수

    Args:
        case_id (str): 케이스 ID

    Returns:
        int: 해당 케이스의 벡터 개수
    """

def delete_by_case(self, case_id: str) -> int:
    """
    케이스별 벡터 삭제

    Args:
        case_id (str): 삭제할 케이스 ID

    Returns:
        int: 삭제된 벡터 개수
    """

def verify_case_isolation(self, case_id: str) -> bool:
    """
    케이스 격리 검증

    Args:
        case_id (str): 검증할 케이스 ID

    Returns:
        bool: 격리되어 있으면 True

    Logic:
        1. case_id로 모든 벡터 조회
        2. 각 벡터의 metadata.case_id 확인
        3. 하나라도 불일치 시 False 반환 (데이터 누수)
    """
```

### StorageManager

통합 스토리지 관리자

```python
from src.storage.storage_manager import StorageManager

manager = StorageManager(
    vector_db_path="./data/chromadb",
    metadata_db_path="./data/metadata.db"
)
```

**메서드**:

```python
def process_file(
    self,
    filepath: str,
    case_id: str
) -> Dict[str, Any]:
    """
    파일 처리 및 저장

    Args:
        filepath (str): 처리할 파일 경로
        case_id (str): 케이스 ID

    Returns:
        Dict:
            - file_id (str): 생성된 파일 ID
            - total_messages (int): 총 메시지 수
            - chunks_stored (int): 저장된 청크 수

    Process:
        1. 파일 타입 감지 (카카오톡/PDF/텍스트)
        2. 파서 선택 및 파싱
        3. 파일 메타데이터 저장
        4. 각 메시지:
           - 임베딩 생성 (OpenAI API)
           - 벡터 저장 (VectorStore)
           - 메타데이터 저장 (MetadataStore)
        5. 에러 시 롤백

    Raises:
        FileNotFoundError: 파일 미존재
        ValueError: 지원하지 않는 파일 타입
        Exception: 임베딩/저장 실패
    """

def search(
    self,
    query: str,
    case_id: str,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    증거 검색

    Args:
        query (str): 검색 쿼리
        case_id (str): 케이스 ID (필수 - 격리)
        top_k (int): 반환 결과 개수

    Returns:
        List[Dict]:
            - content (str): 메시지 내용
            - metadata (Dict): 메타데이터
            - distance (float): 유사도 거리

    Example:
        >>> results = manager.search("외도 증거", "case_001", top_k=5)
        >>> for r in results:
        ...     print(r["content"])
    """

def get_case_summary(self, case_id: str) -> Dict[str, Any]:
    """케이스 요약 정보"""

def get_case_files(self, case_id: str) -> List[EvidenceFile]:
    """케이스 파일 목록"""

def get_case_chunks(self, case_id: str) -> List[EvidenceChunk]:
    """케이스 청크 목록"""
```

---

## Search

### SearchEngine

벡터 검색 + 컨텍스트 확장

```python
from src.storage.search_engine import SearchEngine

engine = SearchEngine(
    vector_store=vector_store,
    metadata_store=metadata_store
)
```

**메서드**:

```python
def search(
    self,
    query: str,
    case_id: str,
    top_k: int = 10,
    context_window: int = 2
) -> List[SearchResult]:
    """
    컨텍스트 확장 검색

    Args:
        query (str): 검색 쿼리
        case_id (str): 케이스 ID
        top_k (int): 반환 결과 개수
        context_window (int): 전후 컨텍스트 개수

    Returns:
        List[SearchResult]:
            - chunk_id, file_id, content, distance
            - timestamp, sender, case_id
            - context_before (List[str]): 이전 메시지
            - context_after (List[str]): 이후 메시지

    Example:
        >>> results = engine.search("외도", "case_001", context_window=2)
        >>> print(results[0].context_before)  # 이전 2개 메시지
        ["직전 메시지 1", "직전 메시지 2"]
    """
```

### HybridSearchEngine

사용자 증거 + 법률 지식 통합 검색

```python
from src.user_rag.hybrid_search import HybridSearchEngine

engine = HybridSearchEngine(
    evidence_search=evidence_search,
    legal_search=legal_search
)
```

**메서드**:

```python
def search(
    self,
    query: str,
    case_id: str,
    top_k: int = 10,
    evidence_only: bool = False,
    legal_only: bool = False
) -> List[HybridResult]:
    """
    통합 검색

    Args:
        query (str): 검색 쿼리
        case_id (str): 케이스 ID
        top_k (int): 반환 결과 개수
        evidence_only (bool): 증거만 검색
        legal_only (bool): 법률만 검색

    Returns:
        List[HybridResult]:
            - source (str): "evidence" or "legal"
            - content (str): 내용
            - distance (float): 유사도 거리
            - metadata (Dict): 추가 정보

    Example:
        >>> results = engine.search("이혼 사유", "case_001")
        >>> for r in results:
        ...     if r.source == "legal":
        ...         print(f"관련 법조문: {r.content}")
        ...     else:
        ...         print(f"관련 증거: {r.content}")
    """
```

---

## Data Models

### Message

파서 출력 기본 모델

```python
from src.parsers.base import Message

@dataclass
class Message:
    content: str                # 메시지 내용
    sender: str                 # 발신자
    timestamp: datetime         # 발신 시간
```

### EvidenceFile

파일 메타데이터

```python
from src.storage.schemas import EvidenceFile

class EvidenceFile(BaseModel):
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: str              # kakaotalk | text | pdf | image
    parsed_at: datetime = Field(default_factory=datetime.now)
    total_messages: int
    case_id: str
    filepath: Optional[str] = None
```

### EvidenceChunk

청크/메시지 메타데이터

```python
from src.storage.schemas import EvidenceChunk

class EvidenceChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str
    content: str
    score: Optional[float] = None
    timestamp: datetime
    sender: str
    vector_id: Optional[str] = None
    case_id: str
```

### SearchResult

검색 결과 모델

```python
from src.storage.schemas import SearchResult

class SearchResult(BaseModel):
    chunk_id: str
    file_id: str
    content: str
    distance: float
    timestamp: datetime
    sender: str
    case_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    context_before: Optional[List[str]] = None
    context_after: Optional[List[str]] = None
```

---

## 사용 예제

### 전체 플로우

```python
from src.storage.storage_manager import StorageManager
from src.analysis.analysis_engine import AnalysisEngine

# 1. 초기화
manager = StorageManager()
analyzer = AnalysisEngine()

# 2. 파일 처리
result = manager.process_file(
    filepath="./evidence/kakao_chat.txt",
    case_id="case_001"
)
print(f"저장 완료: {result['chunks_stored']}개 청크")

# 3. 검색
search_results = manager.search(
    query="외도 증거",
    case_id="case_001",
    top_k=5
)

# 4. 분석
messages = [...]  # 파서로 추출한 메시지
analysis = analyzer.analyze(messages)
print(f"위험도: {analysis.risk_analysis.overall_risk}")

# 5. 케이스 관리
metadata_store = manager.metadata_store
cases = metadata_store.list_cases()
stats = metadata_store.get_case_stats("case_001")
```

---

## 에러 처리

모든 메서드는 다음 예외를 발생시킬 수 있습니다:

- `FileNotFoundError`: 파일 미존재
- `ValueError`: 잘못된 파라미터
- `Exception`: API 호출 실패, 데이터베이스 오류 등

권장 에러 처리:

```python
try:
    result = manager.process_file(filepath, case_id)
except FileNotFoundError:
    print("파일을 찾을 수 없습니다")
except ValueError as e:
    print(f"잘못된 입력: {e}")
except Exception as e:
    print(f"처리 실패: {e}")
    # 롤백 자동 수행됨
```
