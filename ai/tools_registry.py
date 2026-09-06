"""
Registre centralisé et découverte automatique des outils pour BARBATOS.
Permet d'enregistrer des fonctions Python, de générer leurs schémas de documentation
et de les invoquer dynamiquement depuis le Brain ou le Planner.
"""

import asyncio
import inspect
import json
import logging
from typing import Any, Callable, Dict, List, Optional
from system.shell import shell_executor
from system.apps import app_manager
from system.files import file_manager
from system.windows_ops import windows_ops
from core.memory import long_term_memory

logger = logging.getLogger("Barbatos.ToolsRegistry")


class Tool:
    """Représentation d'un outil exécutable par l'IA."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Dict[str, Any],
        is_async: bool = False
    ):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters
        self.is_async = is_async

    async def execute(self, **kwargs) -> Any:
        """Exécute l'outil de façon asynchrone sécurisée."""
        try:
            if self.is_async:
                return await self.func(**kwargs)
            else:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, lambda: self.func(**kwargs))
        except Exception as e:
            logger.error(f"Erreur d'exécution outil '{self.name}': {e}", exc_info=True)
            return {"error": f"Exception lors de l'exécution de {self.name}: {str(e)}"}

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolsRegistry:
    """Registre de tous les outils mis à disposition du LLM."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        is_async: bool = False
    ):
        def decorator(func: Callable):
            tool = Tool(
                name=name,
                description=description,
                func=func,
                parameters=parameters,
                is_async=is_async or inspect.iscoroutinefunction(func)
            )
            self._tools[name] = tool
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def format_tools_for_prompt(self) -> str:
        """Génère une description textuelle soignée de tous les outils pour le prompt système."""
        lines = ["Outils système disponibles :"]
        for tool in self._tools.values():
            params_str = ", ".join([f"{k}: {v.get('type', 'any')}" for k, v in tool.parameters.get("properties", {}).items()])
            lines.append(f"- **{tool.name}({params_str})** : {tool.description}")
        return "\n".join(lines)

    async def execute_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        tool = self.get_tool(name)
        if not tool:
            return {"error": f"Outil inconnu : '{name}'"}
        args = arguments or {}
        return await tool.execute(**args)

    def _register_default_tools(self):
        """Enregistre l'ensemble des outils système de base."""

        # 1. Shell / PowerShell
        self._tools["execute_shell_command"] = Tool(
            name="execute_shell_command",
            description="Exécute une commande PowerShell (Windows) ou Bash (Linux) et retourne stdout et stderr.",
            func=shell_executor.execute,
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "La commande Shell ou PowerShell à exécuter."},
                    "timeout": {"type": "integer", "description": "Délai max en secondes (défaut 45)."}
                },
                "required": ["command"]
            },
            is_async=True
        )

        # 2. Gestion des applications
        self._tools["launch_application"] = Tool(
            name="launch_application",
            description="Lance un programme exécutable, une commande système ou ouvre un fichier/URL avec l'application par défaut.",
            func=app_manager.launch_app,
            parameters={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Nom de l'exécutable, chemin complet ou URL (ex: 'notepad.exe', 'calc.exe', 'https://...')."}
                },
                "required": ["target"]
            },
            is_async=False
        )

        self._tools["terminate_process"] = Tool(
            name="terminate_process",
            description="Ferme ou tue un processus par son nom d'exécutable ou son PID.",
            func=app_manager.kill_process,
            parameters={
                "type": "object",
                "properties": {
                    "name_or_pid": {"type": "string", "description": "Nom du processus (ex: 'notepad.exe') ou PID numérique."}
                },
                "required": ["name_or_pid"]
            },
            is_async=False
        )

        self._tools["list_running_apps"] = Tool(
            name="list_running_apps",
            description="Liste les processus actifs sur le PC avec leur utilisation CPU et mémoire.",
            func=app_manager.list_running_apps,
            parameters={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Nombre max de processus à retourner (défaut 30)."}
                }
            },
            is_async=False
        )

        # 3. Fichiers et dossiers
        self._tools["search_files"] = Tool(
            name="search_files",
            description="Recherche récursivement des fichiers sur le disque selon un dossier et un motif glob.",
            func=file_manager.search_files,
            parameters={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Répertoire racine de recherche (ex: 'C:\\Users', '.')."},
                    "pattern": {"type": "string", "description": "Motif de recherche (ex: '*.txt', '*rapport*')."},
                    "recursive": {"type": "boolean", "description": "Recherche récursive dans les sous-dossiers."}
                },
                "required": ["directory"]
            },
            is_async=False
        )

        self._tools["read_file"] = Tool(
            name="read_file",
            description="Lit le contenu textuel d'un fichier sur le disque.",
            func=file_manager.read_file,
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Chemin absolu ou relatif vers le fichier."}
                },
                "required": ["file_path"]
            },
            is_async=False
        )

        self._tools["write_file"] = Tool(
            name="write_file",
            description="Crée ou met à jour un fichier avec le contenu fourni.",
            func=file_manager.write_file,
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Chemin cible du fichier."},
                    "content": {"type": "string", "description": "Texte à écrire."},
                    "append": {"type": "boolean", "description": "Ajouter à la fin (True) ou écraser (False)."}
                },
                "required": ["file_path", "content"]
            },
            is_async=False
        )

        # 4. Windows Ops & Hardware
        self._tools["take_screenshot"] = Tool(
            name="take_screenshot",
            description="Prend une capture d'écran complète du bureau Windows et retourne le chemin de l'image enregistrée.",
            func=windows_ops.take_screenshot,
            parameters={"type": "object", "properties": {}},
            is_async=False
        )

        self._tools["show_toast_notification"] = Tool(
            name="show_toast_notification",
            description="Affiche une bulle de notification Toast Windows en bas à droite de l'écran.",
            func=windows_ops.show_toast_notification,
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Titre de la notification."},
                    "message": {"type": "string", "description": "Corps du message."}
                },
                "required": ["title", "message"]
            },
            is_async=False
        )

        self._tools["get_hardware_status"] = Tool(
            name="get_hardware_status",
            description="Récupère les métriques matérielles instantanées du PC (CPU %, RAM utilisée, Batterie %).",
            func=windows_ops.get_hardware_metrics,
            parameters={"type": "object", "properties": {}},
            is_async=False
        )

        self._tools["get_clipboard"] = Tool(
            name="get_clipboard",
            description="Lit le texte actuellement présent dans le presse-papier Windows.",
            func=windows_ops.get_clipboard_text,
            parameters={"type": "object", "properties": {}},
            is_async=False
        )

        self._tools["set_clipboard"] = Tool(
            name="set_clipboard",
            description="Copie du texte dans le presse-papier Windows.",
            func=windows_ops.set_clipboard_text,
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Texte à copier."}
                },
                "required": ["text"]
            },
            is_async=False
        )

        # 5. Mémoire persistante
        self._tools["remember_fact"] = Tool(
            name="remember_fact",
            description="Enregistre une information, préférence ou fait durablement dans la mémoire de Barbatos.",
            func=long_term_memory.remember_fact,
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Identifiant clé du fait (ex: 'utilisateur.nom', 'serveur.ip')."},
                    "value": {"type": "string", "description": "Valeur ou description détaillée à retenir."},
                    "category": {"type": "string", "description": "Catégorie (ex: 'preference', 'systeme', 'reseau')."}
                },
                "required": ["key", "value"]
            },
            is_async=False
        )

        self._tools["recall_fact"] = Tool(
            name="recall_fact",
            description="Recherche et extrait des faits ou préférences enregistrés en mémoire.",
            func=long_term_memory.search_facts,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Mot-clé ou clé exacte à rechercher."}
                },
                "required": ["query"]
            },
            is_async=False
        )


tools_registry = ToolsRegistry()
