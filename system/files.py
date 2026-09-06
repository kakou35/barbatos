"""
Gestionnaire d'opérations sur le système de fichiers pour BARBATOS.
Recherche, lecture, écriture, suppression et inspection des répertoires.
"""

import os
from pathlib import Path
import shutil
import time
from typing import List, Dict, Any, Optional


class FileManager:
    """Opérations fichiers et dossiers avec gestion d'erreurs et informations détaillées."""

    @staticmethod
    def search_files(directory: str, pattern: str = "*", recursive: bool = True, limit: int = 50) -> List[Dict[str, Any]]:
        """Recherche des fichiers correspondant à un motif glob."""
        base = Path(directory)
        if not base.exists() or not base.is_dir():
            return []

        results = []
        iterator = base.rglob(pattern) if recursive else base.glob(pattern)

        for p in iterator:
            try:
                stat = p.stat()
                results.append({
                    "name": p.name,
                    "path": str(p.resolve()),
                    "is_dir": p.is_dir(),
                    "size_bytes": stat.st_size if not p.is_dir() else 0,
                    "modified_time": time.ctime(stat.st_mtime)
                })
                if len(results) >= limit:
                    break
            except (PermissionError, FileNotFoundError):
                continue

        return results

    @staticmethod
    def read_file(file_path: str, max_chars: int = 15000) -> Dict[str, Any]:
        """Lit le contenu d'un fichier texte."""
        p = Path(file_path)
        if not p.exists():
            return {"success": False, "error": f"Fichier introuvable : {file_path}", "content": ""}
        if p.is_dir():
            return {"success": False, "error": f"{file_path} est un dossier.", "content": ""}

        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars)
            return {
                "success": True,
                "path": str(p.resolve()),
                "content": content,
                "size_bytes": p.stat().st_size,
                "truncated": p.stat().st_size > max_chars
            }
        except Exception as e:
            return {"success": False, "error": str(e), "content": ""}

    @staticmethod
    def write_file(file_path: str, content: str, append: bool = False) -> Dict[str, Any]:
        """Écrit du contenu dans un fichier."""
        p = Path(file_path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with open(p, mode, encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "message": f"Fichier {'complété' if append else 'créé'} avec succès : {str(p.resolve())}",
                "size_bytes": p.stat().st_size
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_path(path: str) -> Dict[str, Any]:
        """Supprime un fichier ou un dossier."""
        p = Path(path)
        if not p.exists():
            return {"success": False, "error": f"Chemin inexistant : {path}"}

        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return {"success": True, "message": f"Élément supprimé : {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_disk_usage(path: str = "C:\\") -> Dict[str, Any]:
        """Retourne l'espace disque disponible sur un lecteur."""
        try:
            total, used, free = shutil.disk_usage(path)
            gb = 1024 ** 3
            return {
                "drive": path,
                "total_gb": round(total / gb, 2),
                "used_gb": round(used / gb, 2),
                "free_gb": round(free / gb, 2),
                "percent_used": round((used / total) * 100, 1)
            }
        except Exception as e:
            return {"error": str(e)}


file_manager = FileManager()
