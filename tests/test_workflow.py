"""
Tests d'exécution du moteur de workflow (automation.workflow_engine).
"""

import asyncio
from automation.workflow_engine import workflow_engine, WorkflowDefinition, WorkflowStep


def test_workflow_execution():
    async def run_wf():
        step1 = WorkflowStep(
            id="step1",
            name="Lecture Métriques",
            tool="get_hardware_status",
            args={}
        )
        wf = WorkflowDefinition(
            name="Test Workflow",
            description="Workflow de test unitaire",
            steps=[step1]
        )

        result = await workflow_engine.execute_workflow(wf)
        assert result["success"] is True
        assert len(result["steps"]) == 1
        assert result["steps"][0]["step_id"] == "step1"

    asyncio.run(run_wf())


if __name__ == "__main__":
    test_workflow_execution()
    print("Test Workflow validé avec succès !")
