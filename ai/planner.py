"""
Planificateur stratégique de tâches complexes pour BARBATOS.
Décompose une demande de haut niveau en graphe ou séquence d'actions structurées.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ai.llm_client import llm_client
from ai.tools_registry import tools_registry
from config.prompts import PLANNER_PROMPT

logger = logging.getLogger("Barbatos.Planner")


class PlanStep(BaseModel):
    step_id: int
    title: str
    tool: str
    description: str
    dependencies: List[int] = Field(default_factory=list)
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    result: Optional[Any] = None


class ExecutionPlan(BaseModel):
    plan_summary: str
    steps: List[PlanStep] = Field(default_factory=list)


class TaskPlanner:
    """Générateur de plans d'action ordonnés et optimisés."""

    async def create_plan(self, user_goal: str) -> ExecutionPlan:
        """Génère un plan d'action découpé à partir d'une requête utilisateur complexe."""
        tools_desc = tools_registry.format_tools_for_prompt()
        prompt = (
            f"{PLANNER_PROMPT}\n\n"
            f"{tools_desc}\n\n"
            f"COMMANDE UTILISATEUR :\n\"{user_goal}\"\n\n"
            f"Génère le JSON du plan d'action :"
        )

        try:
            raw_response = await llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                format_json=True
            )

            # Nettoyage et extraction JSON
            data = json.loads(raw_response)
            if "steps" not in data:
                data = {"plan_summary": f"Exécution directe de : {user_goal}", "steps": [
                    {"step_id": 1, "title": "Exécution", "tool": "execute_shell_command", "description": user_goal, "dependencies": []}
                ]}

            return ExecutionPlan(**data)

        except Exception as e:
            logger.warning(f"Erreur planification automatique ({e}), repli sur un plan d'étape unique.")
            return ExecutionPlan(
                plan_summary=f"Mission : {user_goal}",
                steps=[
                    PlanStep(
                        step_id=1,
                        title="Traitement de la commande",
                        tool="auto",
                        description=user_goal,
                        dependencies=[]
                    )
                ]
            )


task_planner = TaskPlanner()
