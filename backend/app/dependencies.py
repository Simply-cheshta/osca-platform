from app.agents.graph import AgentOrchestrator
from app.services.llm_service import GeminiService
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.qdrant_service import QdrantService
from app.services.vector_service import VectorService

vector_service = VectorService()
llm_service = GeminiService()
qdrant_service = QdrantService()
matching_service = MatchingService(vector_service, llm_service)
profile_service = ProfileService(vector_service)
agent_orchestrator = AgentOrchestrator(
    vector_service, llm_service, profile_service, matching_service
)
