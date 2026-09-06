"""
Cerveau décisionnel autonome (ReAct Loop) pour BARBATOS.
Cycle perpétuel : Penser -> Agir -> Observer -> S'adapter -> Conclure.
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional
from config.settings import settings
from config.prompts import BARBATOS_SYSTEM_PROMPT
from core.bus import event_bus
from core.state import state_manager, AgentState
from core.memory import short_term_memory, long_term_memory
from ai.llm_client import llm_client
from ai.tools_registry import tools_registry

logger = logging.getLogger("Barbatos.Brain")


class BrainEngine:
    """Moteur de raisonnement autonome de Barbatos."""

    def __init__(self):
        self.max_steps = settings.ai.react_max_steps

    def _extract_json_block(self, text: str) -> Optional[Dict[str, Any]]:
        """Extrait et désérialise un bloc JSON depuis une réponse textuelle brute."""
        # 1. Recherche de blocs ```json ... ```
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 2. Recherche du premier { jusqu'au dernier }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return None

    async def think_and_act(self, user_input: str) -> str:
        """
        Exécute la boucle complète de raisonnement ReAct face à une demande utilisateur.
        """
        await state_manager.set_state(AgentState.THINKING, f"Analyse de la demande : '{user_input[:40]}...'")
        short_term_memory.add_message("user", user_input)

        # Préparation du contexte d'outils
        tools_description = tools_registry.format_tools_for_prompt()
        system_prompt = f"{BARBATOS_SYSTEM_PROMPT}\n\n{tools_description}"

        # Construction de l'historique de la session
        messages: List[Dict[str, str]] = []
        for msg in short_term_memory.get_context():
            messages.append({"role": msg["role"], "content": msg["content"]})

        step_count = 0
        scratchpad = ""

        while step_count < self.max_steps:
            step_count += 1
            await state_manager.set_state(AgentState.THINKING, f"Raisonnement étape {step_count}/{self.max_steps}")

            # Appel au LLM
            try:
                raw_response = await llm_client.chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=settings.ai.temperature
                )
            except Exception as e:
                err_msg = f"Erreur de communication avec le LLM local (Ollama) : {str(e)}"
                logger.error(err_msg)
                await state_manager.set_state(AgentState.ERROR, err_msg)
                return f"[BARBATOS ERREUR] Impossible de joindre le modèle local : {str(e)}. Vérifiez qu'Ollama est actif (`ollama serve`)."

            parsed = self._extract_json_block(raw_response)

            # Si le modèle a répondu en texte libre sans JSON, on tente de le formuler en réponse finale
            if not parsed:
                # Vérifier si c'est une réponse directe
                final_text = raw_response.strip()
                short_term_memory.add_message("assistant", final_text)
                await state_manager.set_state(AgentState.IDLE, "Mission accomplie")
                await event_bus.publish("agent.final_answer", {"answer": final_text}, sender="brain")
                state_manager.record_task_completed()
                return final_text

            thought = parsed.get("thought", "Analyse en cours...")
            await event_bus.publish("agent.thought", {"step": step_count, "thought": thought}, sender="brain")

            # Cas 1 : Réponse finale atteinte
            if "final_answer" in parsed:
                final_answer = parsed["final_answer"]
                short_term_memory.add_message("assistant", final_answer)
                await state_manager.set_state(AgentState.IDLE, "En veille")
                await event_bus.publish("agent.final_answer", {"answer": final_answer}, sender="brain")
                state_manager.record_task_completed()
                return final_answer

            # Cas 2 : Appel d'outil
            action = parsed.get("action")
            action_input = parsed.get("action_input", {})

            if not action:
                # Pas d'action spécifiée, on conclut
                final_answer = thought
                short_term_memory.add_message("assistant", final_answer)
                await state_manager.set_state(AgentState.IDLE, "En veille")
                return final_answer

            await state_manager.set_state(AgentState.EXECUTING, f"Outil : {action}")
            await event_bus.publish(
                "agent.tool_called",
                {"step": step_count, "tool": action, "input": action_input, "thought": thought},
                sender="brain"
            )

            # Exécution de l'outil
            observation = await tools_registry.execute_tool(action, action_input)

            # Formatage de l'observation
            obs_str = json.dumps(observation, ensure_ascii=False) if isinstance(observation, (dict, list)) else str(observation)
            if len(obs_str) > 3000:
                obs_str = obs_str[:3000] + "... [tronqué]"

            await event_bus.publish(
                "agent.tool_result",
                {"step": step_count, "tool": action, "result": observation},
                sender="brain"
            )

            # Ajout de l'interaction dans le fil de discussion pour la prochaine itération
            messages.append({
                "role": "assistant",
                "content": json.dumps(parsed, ensure_ascii=False)
            })
            messages.append({
                "role": "user",
                "content": f"OBSERVATION DE L'OUTIL '{action}' :\n{obs_str}\n\nContinue ton analyse ou fournis la 'final_answer'."
            })

        # Si le nombre max d'étapes est dépassé
        fallback_msg = "Nombre d'itérations maximal atteint sans réponse finale concluante. Voici les dernières observations recueillies."
        await state_manager.set_state(AgentState.IDLE, "Timeout étapes")
        return fallback_msg


brain = BrainEngine()
