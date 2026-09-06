"""
Client SSH asynchrone pour la gestion de machines distantes (Linux / serveurs) via BARBATOS.
Utilise paramiko pour exécuter des commandes et transférer des fichiers via SFTP.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import paramiko

logger = logging.getLogger("Barbatos.SSH")


class RemoteSSHClient:
    """Gestionnaire de connexions et commandes SSH distantes."""

    async def execute_remote_command(
        self,
        host: str,
        command: str,
        user: str,
        password: Optional[str] = None,
        key_filename: Optional[str] = None,
        port: int = 22,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Exécute une commande sur un serveur distant sans bloquer la boucle principale."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._sync_execute(host, command, user, password, key_filename, port, timeout)
        )

    def _sync_execute(
        self,
        host: str,
        command: str,
        user: str,
        password: Optional[str],
        key_filename: Optional[str],
        port: int,
        timeout: int
    ) -> Dict[str, Any]:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=host,
                port=port,
                username=user,
                password=password,
                key_filename=key_filename,
                timeout=timeout
            )
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            out_str = stdout.read().decode("utf-8", errors="replace").strip()
            err_str = stderr.read().decode("utf-8", errors="replace").strip()
            exit_code = stdout.channel.recv_exit_status()

            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": out_str,
                "stderr": err_str,
                "host": host
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Erreur SSH vers {host}: {str(e)}",
                "host": host
            }
        finally:
            client.close()


ssh_client = RemoteSSHClient()
