"""
Configuration globale pour l'agent Tech Scout.
Contient les paramètres réseau, les en-têtes HTTP et les règles par défaut.
"""

import os
from dataclasses import dataclass

# En-têtes HTTP réalistes pour éviter les blocages de scraping
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Timeout des requêtes HTTP (en secondes)
REQUEST_TIMEOUT = 12

# Nom du fichier de rapport final
DEFAULT_REPORT_FILENAME = "tech_scout_report.md"


@dataclass
class AgentConfig:
    """Paramètres d'exécution de l'agent Tech Scout."""
    auto_approve: bool = False      # Si True, saute l'étape de confirmation manuelle
    max_tools_to_search: int = 15   # Limite raisonnable pour éviter le flood
    verbose: bool = True            # Logs détaillés dans la console
