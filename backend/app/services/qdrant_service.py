from typing import Optional

from app.core.config import settings


class QdrantService:
    """Optional Qdrant integration. Falls back gracefully when not configured."""

    COLLECTION = "osca_issues"
    VECTOR_SIZE = 384

    def __init__(self):
        self._client = None
        self._available = bool(settings.QDRANT_URL)

    def _get_client(self):
        if not self._available:
            return None
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import Distance, VectorParams

                self._client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY or None,
                )
                collections = [c.name for c in self._client.get_collections().collections]
                if self.COLLECTION not in collections:
                    self._client.create_collection(
                        collection_name=self.COLLECTION,
                        vectors_config=VectorParams(size=self.VECTOR_SIZE, distance=Distance.COSINE),
                    )
            except Exception:
                self._available = False
                return None
        return self._client

    def upsert_issue(self, issue_id: str, vector: list[float], payload: dict) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            from qdrant_client.models import PointStruct
            client.upsert(
                collection_name=self.COLLECTION,
                points=[PointStruct(id=issue_id, vector=vector, payload=payload)],
            )
            return True
        except Exception:
            return False

    def search_similar(
        self,
        query_vector: list[float],
        top_k: int = 20,
        language_filter: Optional[str] = None,
    ) -> list[dict]:
        client = self._get_client()
        if not client:
            return []
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            query_filter = None
            if language_filter:
                query_filter = Filter(
                    must=[FieldCondition(key="language", match=MatchValue(value=language_filter))]
                )
            results = client.search(
                collection_name=self.COLLECTION,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter,
            )
            return [{"id": r.id, "score": r.score, **r.payload} for r in results]
        except Exception:
            return []

    @property
    def is_available(self) -> bool:
        return self._available and self._get_client() is not None
