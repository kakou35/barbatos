"""
Gestionnaire de processus et d'applications PC pour BARBATOS.
Permet d'ouvrir, fermer, surveiller et lister les programmes du système d'exploitation.
"""

import os
import subprocess
import psutil
from typing import List, Dict, Any, Optional


class AppManager:
    """Contrôleur de programmes et de processus système."""

    @staticmethod
    def list_running_apps(limit: int = 40) -> List[Dict[str, Any]]:
        """Liste les processus applicatifs en cours d'exécution avec utilisation CPU/RAM."""
        apps = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                info = proc.info
                # Filtrer les processus inactifs ou systèmes triviaux pour une meilleure lisibilité
                if info['name'] and info['status'] == psutil.STATUS_RUNNING:
                    apps.append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "cpu_percent": round(info['cpu_percent'] or 0.0, 1),
                        "memory_percent": round(info['memory_percent'] or 0.0, 1),
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Trier par consommation mémoire décroissante
        apps.sort(key=lambda x: x["memory_percent"], reverse=True)
        return apps[:limit]

    @staticmethod
    def launch_app(target: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Lance une application ou ouvre un fichier avec le programme associé."""
        try:
            full_args = [target] + (args or [])
            if os.name == 'nt':
                # Utilise os.startfile pour les applications Windows courantes
                if not args and (target.endswith(".exe") or "." in target or os.path.exists(target)):
                    os.startfile(target)
                else:
                    subprocess.Popen(full_args, shell=True)
            else:
                subprocess.Popen(full_args)

            return {
                "success": True,
                "message": f"Application lancée avec succès : {target}",
                "target": target,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Échec du lancement de {target} : {str(e)}",
                "target": target,
            }

    @staticmethod
    def kill_process(name_or_pid: str) -> Dict[str, Any]:
        """Arrête un processus par son PID ou son nom d'exécutable."""
        killed = []
        try:
            # Si c'est un PID numérique
            if str(name_or_pid).isdigit():
                pid = int(name_or_pid)
                p = psutil.Process(pid)
                p_name = p.name()
                p.terminate()
                return {
                    "success": True,
                    "message": f"Processus {p_name} (PID: {pid}) arrêté.",
                    "killed_pids": [pid]
                }

            # Sinon recherche par nom
            target_name = name_or_pid.lower()
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if target_name in proc.info['name'].lower():
                        proc.terminate()
                        killed.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if killed:
                return {
                    "success": True,
                    "message": f"{len(killed)} processus arrêtés : {', '.join(killed)}",
                    "killed": killed
                }
            else:
                return {
                    "success": False,
                    "message": f"Aucun processus trouvé correspondant à '{name_or_pid}'.",
                    "killed": []
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur lors de l'arrêt du processus : {str(e)}",
                "killed": []
            }


app_manager = AppManager()
