"""
Sous-agent de navigation autonome (Browser Sub-agent).
Mission :
1. Effectuer une recherche web rapide pour chaque outil identifié.
2. Détecter le site web officiel réel et extraire une URL propre (non sponsorisée, sans redirections).
3. Enrichir la description et la catégorisation.
"""

import re
import urllib.parse
import time
from typing import Optional, List
import requests
from bs4 import BeautifulSoup
from tech_scout.config import DEFAULT_HEADERS, REQUEST_TIMEOUT
from tech_scout.analyzer import DiscoveredTool

# Table de correspondance de référence pour les outils incontournables (vitesse & exactitude maximale)
OFFICIAL_URL_DIRECTORY = {
    "cursor": "https://www.cursor.com",
    "windsurf": "https://codeium.com/windsurf",
    "v0": "https://v0.dev",
    "bolt.new": "https://bolt.new",
    "replit": "https://replit.com",
    "github copilot": "https://github.com/features/copilot",
    "chatgpt": "https://chatgpt.com",
    "claude": "https://claude.ai",
    "gemini": "https://gemini.google.com",
    "deepseek": "https://www.deepseek.com",
    "mistral": "https://mistral.ai",
    "llama": "https://www.llama.com",
    "ollama": "https://ollama.com",
    "langchain": "https://www.langchain.com",
    "llamaindex": "https://www.llamaindex.ai",
    "crewai": "https://www.crewai.com",
    "autogen": "https://microsoft.github.io/autogen/",
    "hugging face": "https://huggingface.co",
    "transformers": "https://huggingface.co/docs/transformers",
    "next.js": "https://nextjs.org",
    "react": "https://react.dev",
    "vue": "https://vuejs.org",
    "svelte": "https://svelte.dev",
    "fastapi": "https://fastapi.tiangolo.com",
    "flask": "https://flask.palletsprojects.com",
    "django": "https://www.djangoproject.com",
    "tailwind": "https://tailwindcss.com",
    "shadcn/ui": "https://ui.shadcn.com",
    "supabase": "https://supabase.com",
    "firebase": "https://firebase.google.com",
    "docker": "https://www.docker.com",
    "kubernetes": "https://kubernetes.io",
    "postgresql": "https://www.postgresql.org",
    "sqlite": "https://www.sqlite.org",
    "qdrant": "https://qdrant.tech",
    "chromadb": "https://www.trychroma.com",
    "pinecone": "https://www.pinecone.io",
    "midjourney": "https://www.midjourney.com",
    "comfyui": "https://www.comfy.org",
    "figma": "https://www.figma.com",
}

# Domaines à ignorer pour trouver le site officiel (moteurs, réseaux sociaux, annuaires génériques)
EXCLUDED_DOMAINS = {
    "google.com", "google.fr", "bing.com", "duckduckgo.com", "yahoo.com",
    "facebook.com", "twitter.com", "x.com", "instagram.com", "linkedin.com",
    "youtube.com", "pinterest.com", "reddit.com", "quora.com", "tiktok.com",
    "wikipedia.org", "medium.com"
}


def clean_url(raw_url: str) -> str:
    """Nettoie une URL en supprimant les paramètres de tracking (utm_*, ref, etc.)."""
    parsed = urllib.parse.urlparse(raw_url)
    # Reconstruire sans query string parasite
    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    return clean if clean else raw_url


def _search_ddg_package(query: str) -> List[str]:
    """Recherche via le package duckduckgo_search si présent."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            urls = []
            for r in results:
                href = r.get("href") or r.get("link")
                if href:
                    urls.append(href)
            return urls
    except Exception:
        return []


def _search_ddg_html(query: str) -> List[str]:
    """Recherche alternative directe via DuckDuckGo HTML Lite (zéro dépendance externe)."""
    try:
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query}
        resp = requests.post(url, data=data, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            urls = []
            for a in soup.find_all("a", class_="result__url"):
                href = a.get("href", "").strip()
                # DuckDuckGo emballe parfois les URLs dans /l/?uddg=...
                if "uddg=" in href:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if "uddg" in qs:
                        href = qs["uddg"][0]
                if href.startswith("http"):
                    urls.append(href)
            return urls
    except Exception:
        pass
    return []


class BrowserSubAgent:
    """
    Sous-agent spécialisé dans la navigation web et la recherche ciblée.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def log(self, message: str) -> None:
        if self.verbose:
            print(f"  🤖 [Browser Sub-Agent] {message}")

    def find_official_website(self, tool_name: str) -> str:
        """
        Recherche le site officiel propre pour un outil donné.
        """
        lower_name = tool_name.lower().strip()

        # 1. Vérification dans l'annuaire de référence (résultat immédiat et certifié)
        if lower_name in OFFICIAL_URL_DIRECTORY:
            self.log(f"Résolution directe certifiée pour '{tool_name}' -> {OFFICIAL_URL_DIRECTORY[lower_name]}")
            return OFFICIAL_URL_DIRECTORY[lower_name]

        self.log(f"Recherche web active pour '{tool_name}'...")
        query = f"{tool_name} official website software"

        # 2. Exécution de la recherche
        urls = _search_ddg_package(query)
        if not urls:
            urls = _search_ddg_html(query)

        # 3. Filtrage intelligent des résultats pour identifier le site officiel
        for url in urls:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]

            # Vérifier si ce n'est pas un domaine parasite ou un réseau social
            is_excluded = any(exc in domain for exc in EXCLUDED_DOMAINS)
            if not is_excluded:
                cleaned = clean_url(url)
                self.log(f"Site officiel détecté pour '{tool_name}' : {cleaned}")
                return cleaned

        # Si aucune URL n'est trouvée, fallback propre
        fallback = f"https://www.google.com/search?q={urllib.parse.quote(tool_name + ' tool')}"
        self.log(f"Aucun site direct isolé pour '{tool_name}'.")
        return fallback

    def enrich_tool(self, tool: DiscoveredTool) -> DiscoveredTool:
        """
        Prend un outil et enrichit son URL officielle et ses métadonnées.
        """
        official_url = self.find_official_website(tool.name)
        tool.official_url = official_url
        if not tool.description:
            tool.description = f"Outil technologique et solution logicielle pour {tool.name}."
        return tool

    def run_enrichment(self, tools: List[DiscoveredTool]) -> List[DiscoveredTool]:
        """
        Exécute la navigation autonome en série pour la liste d'outils.
        """
        print(f"\n🌐 Démarrage du Browser Sub-agent pour {len(tools)} outil(s)...")
        enriched = []
        for tool in tools:
            self.enrich_tool(tool)
            enriched.append(tool)
            time.sleep(0.3)  # Respect des cadences de requêtes
        print(f"✨ Navigation terminée avec succès pour tous les outils !\n")
        return enriched
