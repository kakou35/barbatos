"""
Gestionnaire de macros système pour BARBATOS.
Permet d'exécuter des séquences d'actions prédéfinies ou enregistrées d'un simple appel.
"""

import asyncio
from typing import Dict, Any, List
from ai.tools_registry import tools_registry


class MacroManager:
    """Enregistre et exécute des macros système courtes."""

    def __init__(self):
        self._macros: Dict[str, List[Dict[str, Any]]] = {}
        self._register_default_macros()

    def _register_default_macros(self):
        # Macro 1 : Diagnostic rapide du système
        self._macros["quick_diagnostic"] = [
            {"tool": "get_hardware_status", "args": {}},
            {"tool": "list_running_apps", "args": {"limit": 10}},
        ]

        # Macro 2 : Capture & Notification
        self._macros["capture_desktop"] = [
            {"tool": "take_screenshot", "args": {}},
            {"tool": "show_toast_notification", "args": {"title": "BARBATOS", "message": "Capture du bureau effectuée avec succès."}}
        ]

    def register_macro(self, name: str, actions: List[Dict[str, Any]]):
        self._macros[name] = actions

    async def run_macro(self, name: str) -> List[Any]:
        """Exécute les actions d'une macro en séquence."""
        actions = self._macros.get(name)
        if not actions:
            return [{"error": f"Macro '{name}' inconnue."}]

        results = []
        for action in actions:
            tool_name = action.get("tool")
            args = action.get("args", {})
            res = await tools_registry.execute_tool(tool_name, args)
            results.append(res)

        return results


macro_manager = MacroManager()
