"""
RAG 기반 법률 조항 검색 및 추천 시스템
"""

from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime
import asyncio

import pinecone
from sentence_transformers import SentenceTransformer
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings
from app.models.law import Law


class LegalRAGSystem:
    """법률 RAG (Retrieval Augmented Generation) 시스템"""

    def __init__(self):
        # Pinecone 초기화
        pinecone.init(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        self.index = pinecone.Index(settings.PINECONE_INDEX_NAME)

        # 임베딩 모델 초기화
        self.embedder = SentenceTransformer('jhgan/ko-sroberta-multitask')  # 한국어 특화 모델
        self.openai_embedder = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)

        # 텍스트 분할기
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            length_function=len
        )

    async def index_law(self, law: Law) -> bool:
        """
        법률 조항을 벡터 DB에 인덱싱

        Args:
            law: 법률 조항 모델

        Returns:
            성공 여부
        """
        try:
            # 텍스트 준비
            text = self._prepare_law_text(law)

            # 텍스트 분할
            chunks = self.text_splitter.split_text(text)

            # 벡터 생성
            vectors = []
            for i, chunk in enumerate(chunks):
                embedding = self._generate_embedding(chunk)

                vector_id = f"{law.law_id}_{law.article_number}_{i}"
                metadata = {
                    "law_id": law.law_id,
                    "law_name": law.law_name,
                    "category": law.category,
                    "article_number": law.article_number,
                    "article_title": law.article_title,
                    "chunk_text": chunk,
                    "full_text": text,
                    "enforcement_date": law.enforcement_date.isoformat() if law.enforcement_date else None,
                    "keywords": law.keywords or [],
                    "importance_score": law.importance_score
                }

                vectors.append((vector_id, embedding.tolist(), metadata))

            # Pinecone에 업로드
            self.index.upsert(vectors=vectors)

            return True

        except Exception as e:
            print(f"Error indexing law: {e}")
            return False

    async def search_laws(
        self,
        query: str,
        top_k: int = 10,
        category: Optional[str] = None,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        법률 조항 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            category: 법률 카테고리 필터
            min_score: 최소 유사도 점수

        Returns:
            검색 결과 목록
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self._generate_embedding(query)

            # 필터 설정
            filter_dict = {}
            if category:
                filter_dict["category"] = category

            # Pinecone 검색
            results = self.index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )

            # 결과 처리
            search_results = []
            for match in results.matches:
                if match.score >= min_score:
                    result = {
                        "score": match.score,
                        "law_id": match.metadata.get("law_id"),
                        "law_name": match.metadata.get("law_name"),
                        "article_number": match.metadata.get("article_number"),
                        "article_title": match.metadata.get("article_title"),
                        "text": match.metadata.get("chunk_text"),
                        "category": match.metadata.get("category"),
                        "keywords": match.metadata.get("keywords", [])
                    }
                    search_results.append(result)

            # 후처리: 중복 제거 및 정렬
            search_results = self._postprocess_results(search_results)

            return search_results

        except Exception as e:
            print(f"Error searching laws: {e}")
            return []

    async def get_recommendations(
        self,
        context: str,
        document_type: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        문맥 기반 법률 조항 추천

        Args:
            context: 문서 컨텍스트
            document_type: 문서 타입
            top_k: 추천할 조항 수

        Returns:
            추천 법률 조항 목록
        """
        try:
            # 컨텍스트 분석
            key_terms = self._extract_key_terms(context)

            # 문서 타입별 관련 법률 카테고리
            relevant_categories = self._get_relevant_categories(document_type)

            # 다중 쿼리 생성
            queries = self._generate_multiple_queries(context, key_terms)

            # 각 쿼리로 검색
            all_results = []
            for query in queries:
                for category in relevant_categories:
                    results = await self.search_laws(
                        query=query,
                        top_k=top_k,
                        category=category,
                        min_score=0.6
                    )
                    all_results.extend(results)

            # 결과 통합 및 순위 재조정
            recommendations = self._rerank_results(all_results, context)

            return recommendations[:top_k]

        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return []

    async def find_similar_cases(
        self,
        document_content: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        유사 판례 검색

        Args:
            document_content: 문서 내용
            top_k: 반환할 판례 수

        Returns:
            유사 판례 목록
        """
        # 문서 임베딩 생성
        doc_embedding = self._generate_embedding(document_content)

        # 판례 DB에서 검색 (별도 인덱스 사용)
        case_index = pinecone.Index("legal-cases")

        results = case_index.query(
            vector=doc_embedding.tolist(),
            top_k=top_k,
            include_metadata=True
        )

        similar_cases = []
        for match in results.matches:
            case = {
                "case_number": match.metadata.get("case_number"),
                "court_name": match.metadata.get("court_name"),
                "judgment_date": match.metadata.get("judgment_date"),
                "summary": match.metadata.get("summary"),
                "similarity_score": match.score,
                "related_laws": match.metadata.get("related_laws", [])
            }
            similar_cases.append(case)

        return similar_cases

    def _prepare_law_text(self, law: Law) -> str:
        """법률 텍스트 준비"""
        text_parts = []

        if law.law_name:
            text_parts.append(f"법령명: {law.law_name}")
        if law.article_number:
            text_parts.append(f"조항: {law.article_number}")
        if law.article_title:
            text_parts.append(f"제목: {law.article_title}")
        if law.article_content:
            text_parts.append(f"내용: {law.article_content}")
        if law.keywords:
            text_parts.append(f"키워드: {', '.join(law.keywords)}")

        return "\n".join(text_parts)

    def _generate_embedding(self, text: str) -> np.ndarray:
        """텍스트 임베딩 생성"""
        # 한국어 특화 모델 사용
        embedding = self.embedder.encode(text)
        return embedding

    def _extract_key_terms(self, text: str) -> List[str]:
        """핵심 용어 추출"""
        # 간단한 키워드 추출 (실제로는 더 정교한 방법 사용)
        legal_terms = [
            "계약", "손해배상", "해지", "위약금", "보증", "임대", "매매",
            "고용", "해고", "임금", "근로", "상속", "유언", "이혼", "양육권"
        ]

        found_terms = []
        for term in legal_terms:
            if term in text:
                found_terms.append(term)

        return found_terms

    def _get_relevant_categories(self, document_type: str) -> List[str]:
        """문서 타입별 관련 법률 카테고리"""
        category_mapping = {
            "contract": ["민법", "상법"],
            "employment": ["근로기준법", "노동법"],
            "real_estate": ["민법", "부동산법", "건축법"],
            "lawsuit": ["민사소송법", "형사소송법"],
            "family": ["민법", "가족법"],
            "business": ["상법", "회사법", "세법"]
        }

        return category_mapping.get(document_type, ["민법"])

    def _generate_multiple_queries(self, context: str, key_terms: List[str]) -> List[str]:
        """다중 쿼리 생성"""
        queries = [context[:500]]  # 원본 컨텍스트

        # 핵심 용어 조합
        if key_terms:
            queries.append(" ".join(key_terms))

        # 질문 형태로 변환
        question_formats = [
            f"{context[:200]}에 관한 법률 조항",
            f"{' '.join(key_terms[:3])} 관련 규정"
        ]
        queries.extend(question_formats)

        return queries

    def _postprocess_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """검색 결과 후처리"""
        # 법률 ID와 조항 번호로 그룹화
        grouped = {}
        for result in results:
            key = f"{result['law_id']}_{result['article_number']}"
            if key not in grouped or result['score'] > grouped[key]['score']:
                grouped[key] = result

        # 점수 순으로 정렬
        sorted_results = sorted(grouped.values(), key=lambda x: x['score'], reverse=True)

        return sorted_results

    def _rerank_results(
        self,
        results: List[Dict[str, Any]],
        context: str
    ) -> List[Dict[str, Any]]:
        """결과 재순위 조정"""
        if not results:
            return []

        # 컨텍스트 임베딩
        context_embedding = self._generate_embedding(context)

        # 각 결과의 재점수 계산
        for result in results:
            # 텍스트 임베딩
            result_embedding = self._generate_embedding(result['text'])

            # 코사인 유사도 계산
            similarity = cosine_similarity(
                [context_embedding],
                [result_embedding]
            )[0][0]

            # 기존 점수와 결합
            result['final_score'] = (result['score'] * 0.6) + (similarity * 0.4)

        # 최종 점수로 정렬
        reranked = sorted(results, key=lambda x: x['final_score'], reverse=True)

        # 중복 제거
        seen = set()
        unique_results = []
        for result in reranked:
            key = f"{result['law_id']}_{result['article_number']}"
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        return unique_results


class LegalSearchEngine:
    """법률 검색 엔진"""

    def __init__(self):
        self.rag_system = LegalRAGSystem()

    async def hybrid_search(
        self,
        query: str,
        search_type: str = "all",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        하이브리드 검색 (키워드 + 의미 검색)

        Args:
            query: 검색 쿼리
            search_type: 검색 타입 (all, laws, cases, interpretations)
            filters: 필터 조건

        Returns:
            통합 검색 결과
        """
        results = {
            "laws": [],
            "cases": [],
            "interpretations": [],
            "recommendations": []
        }

        # 병렬 검색 실행
        tasks = []

        if search_type in ["all", "laws"]:
            tasks.append(self.rag_system.search_laws(query, top_k=10))

        if search_type in ["all", "cases"]:
            tasks.append(self.rag_system.find_similar_cases(query, top_k=5))

        # 비동기 실행
        if tasks:
            search_results = await asyncio.gather(*tasks)

            if search_type in ["all", "laws"] and len(search_results) > 0:
                results["laws"] = search_results[0]

            if search_type in ["all", "cases"] and len(search_results) > 1:
                results["cases"] = search_results[1]

        # 추천 생성
        if results["laws"]:
            recommendations = await self._generate_recommendations(
                query,
                results["laws"]
            )
            results["recommendations"] = recommendations

        return results

    async def _generate_recommendations(
        self,
        query: str,
        law_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """검색 결과 기반 추천"""
        recommendations = []

        # 관련 법률 수집
        related_laws = set()
        for result in law_results[:3]:
            if result.get("related_laws"):
                related_laws.update(result["related_laws"])

        # 관련 법률 검색
        for law_id in list(related_laws)[:5]:
            # 실제로는 DB에서 조회
            recommendation = {
                "type": "related_law",
                "law_id": law_id,
                "reason": "검색 결과와 관련된 법률"
            }
            recommendations.append(recommendation)

        return recommendations