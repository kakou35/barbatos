"""
Moteur de workflows automatisés multi-étapes déclaratifs (YAML/JSON) pour BARBATOS.
Permet d'enchaîner des actions système, des appels d'outils et des analyses LLM avec passage de variables.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
from pydantic import BaseModel, Field
from ai.tools_registry import tools_registry
from core.bus import event_bus

logger = logging.getLogger("Barbatos.Workflow")


class WorkflowStep(BaseModel):
    id: str
    name: str
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)
    continue_on_error: bool = False


class WorkflowDefinition(BaseModel):
    name: str
    description: str
    version: str = "1.0"
    steps: List[WorkflowStep]


class WorkflowEngine:
    """Exécuteur de workflows séquentiels ou conditionnels."""

    def __init__(self):
        self._running_workflows: Dict[str, Any] = {}

    def load_from_yaml(self, file_path: str) -> WorkflowDefinition:
        """Charge une définition de workflow depuis un fichier YAML."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return WorkflowDefinition(**data)

    async def execute_workflow(self, workflow: WorkflowDefinition) -> Dict[str, Any]:
        """Exécute les étapes ordonnées du workflow et transmet le contexte entre étapes."""
        logger.info(f"Démarrage du workflow : {workflow.name}")
        await event_bus.publish("workflow.started", {"name": workflow.name}, sender="workflow_engine")

        context: Dict[str, Any] = {}
        step_results: List[Dict[str, Any]] = []

        for step in workflow.steps:
            logger.info(f"Exécution de l'étape : [{step.id}] {step.name}")
            await event_bus.publish("workflow.step_started", {"step_id": step.id, "name": step.name}, sender="workflow_engine")

            # Substitution basique des variables du contexte dans les arguments
            resolved_args = {}
            for k, v in step.args.items():
                if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
                    var_name = v[2:-2].strip()
                    resolved_args[k] = context.get(var_name, v)
                else:
                    resolved_args[k] = v

            # Exécution de l'outil
            result = await tools_registry.execute_tool(step.tool, resolved_args)
            context[step.id] = result

            success = True
            if isinstance(result, dict) and "error" in result:
                success = False

            step_results.append({
                "step_id": step.id,
                "name": step.name,
                "success": success,
                "result": result
            })

            await event_bus.publish(
                "workflow.step_finished",
                {"step_id": step.id, "success": success, "result": result},
                sender="workflow_engine"
            )

            if not success and not step.continue_on_error:
                logger.error(f"Arrêt du workflow '{workflow.name}' à l'étape {step.id} en raison d'une erreur.")
                break

        overall_success = all(s["success"] for s in step_results)
        await event_bus.publish(
            "workflow.completed",
            {"name": workflow.name, "success": overall_success},
            sender="workflow_engine"
        )

        return {
            "workflow_name": workflow.name,
            "success": overall_success,
            "steps": step_results,
            "context": context
        }


workflow_engine = WorkflowEngine()
