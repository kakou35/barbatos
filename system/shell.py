"""
Exécuteur sécurisé de commandes Shell (PowerShell sous Windows, Bash sous Linux) pour BARBATOS.
"""

import asyncio
import os
import platform
import subprocess
from typing import Dict, Any, Optional
from config.settings import settings


class SafeShellExecutor:
    """Exécute des commandes système avec surveillance, timeouts et vérification de sécurité."""

    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.blacklist = [cmd.lower() for cmd in settings.security.dangerous_commands_blacklist]

    def is_command_safe(self, command: str) -> bool:
        """Vérifie si la commande contient des séquences dangereuses répertoriées."""
        cmd_lower = command.lower()
        for dangerous in self.blacklist:
            if dangerous in cmd_lower:
                return False
        return True

    async def execute(self, command: str, timeout: int = 45, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Exécute la commande de manière asynchrone sans bloquer la boucle d'événements.
        Sous Windows, utilise PowerShell en arrière-plan.
        Sous Linux/macOS, utilise Bash ou sh.
        """
        if not self.is_command_safe(command):
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"COMMANDE BLOQUÉE PAR LA SÉCURITÉ : Détection d'un motif interdit.",
                "command": command,
            }

        try:
            if self.is_windows:
                # Exécution sous PowerShell avec encodage UTF-8 forcé
                proc = await asyncio.create_subprocess_exec(
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-OutputFormat", "Text",
                    "-Command",
                    f"$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; {command}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd or os.getcwd()
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    "/bin/bash",
                    "-c",
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd or os.getcwd()
                )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            stdout_str = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()

            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "command": command,
            }

        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Délai d'exécution dépassé ({timeout}s). Commande interrompue.",
                "command": command,
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Erreur d'exécution : {str(e)}",
                "command": command,
            }


shell_executor = SafeShellExecutor()
