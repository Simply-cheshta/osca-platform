import json
import time
from typing import Optional

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agents.nodes import make_nodes
from app.agents.state import OSCAState
from app.models.agent_run import AgentRun
from app.services.llm_service import GeminiService
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.vector_service import VectorService


class AgentOrchestrator:
    def __init__(
        self,
        vector_service: VectorService,
        llm_service: GeminiService,
        profile_service: ProfileService,
        matching_service: MatchingService,
    ):
        self.vector_service = vector_service
        self.llm_service = llm_service
        self.profile_service = profile_service
        self.matching_service = matching_service
        self._graph = self._build_graph()

    def _build_graph(self):
        nodes = make_nodes(
            self.vector_service,
            self.llm_service,
            self.profile_service,
            self.matching_service,
        )
        workflow = StateGraph(OSCAState)
        workflow.add_node("profile", nodes["profile"])
        workflow.add_node("discover_issues", nodes["discover_issues"])
        workflow.add_node("match", nodes["match"])
        workflow.add_node("learning_gaps", nodes["learning_gaps"])
        workflow.add_node("codebase", nodes["codebase"])

        workflow.set_entry_point("profile")
        workflow.add_edge("profile", "discover_issues")
        workflow.add_edge("discover_issues", "match")
        workflow.add_edge("match", "codebase")
        workflow.add_edge("codebase", "learning_gaps")
        workflow.add_edge("learning_gaps", END)

        return workflow.compile()

    async def run_full_match(
        self,
        user_id: int,
        github_token: str,
        db: Session,
    ) -> dict:
        run = AgentRun(user_id=user_id, workflow_type="full_match", status="running")
        db.add(run)
        db.commit()
        db.refresh(run)

        start = time.time()
        initial_state: OSCAState = {
            "user_id": user_id,
            "github_token": github_token,
            "errors": [],
        }

        try:
            result = await self._graph.ainvoke(initial_state)
            duration_ms = int((time.time() - start) * 1000)

            run.status = "completed"
            run.duration_ms = duration_ms
            run.state_snapshot = json.dumps({
                "match_count": len(result.get("ranked_matches", [])),
                "learning_gaps": result.get("learning_gaps", []),
            })
            db.commit()

            return {
                "run_id": run.id,
                "status": "completed",
                "duration_ms": duration_ms,
                "ranked_matches": result.get("ranked_matches", []),
                "learning_gaps": result.get("learning_gaps", []),
                "learning_resources": result.get("learning_resources", []),
                "codebase_insights": result.get("codebase_insights", {}),
                "skill_profile": result.get("skill_profile", {}),
            }
        except Exception as e:
            run.status = "failed"
            run.state_snapshot = json.dumps({"error": str(e)})
            db.commit()
            raise

    def get_run(self, run_id: int, db: Session) -> Optional[AgentRun]:
        return db.query(AgentRun).filter(AgentRun.id == run_id).first()
