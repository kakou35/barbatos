"""
Module d'analyse : identifie tous les outils tech, frameworks, logiciels et IA.
Dispose d'une approche hybride :
1. Extraction intelligente par LLM (si GEMINI_API_KEY ou OPENAI_API_KEY disponible).
2. Analyse heuristique & reconnaissance d'entités technologiques embarquée (Zero-Config).
"""

import os
import re
import json
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class DiscoveredTool:
    """Représente un outil tech détecté dans le contenu."""
    name: str
    category: str = "Tech / Inconnue"
    description: str = ""
    official_url: str = ""


# Base de connaissances heuristique pour détection locale instantanée
KNOWN_TECH_CATALOG: Dict[str, Dict[str, str]] = {
    # Éditeurs & IDEs IA
    "cursor": {"category": "Dev / IDE IA", "desc": "Éditeur de code assisté par IA basé sur VS Code."},
    "windsurf": {"category": "Dev / IDE IA", "desc": "IDE nouvelle génération propulsé par des flux de travail agentiques."},
    "v0": {"category": "IA / UI Gen", "desc": "Générateur d'interfaces frontend React/Tailwind par Vercel."},
    "bolt.new": {"category": "Dev / Fullstack IA", "desc": "Environnement de développement fullstack dans le navigateur assisté par IA."},
    "replit": {"category": "Dev / Cloud IDE", "desc": "Plateforme de développement et déploiement collaboratif en ligne."},
    "github copilot": {"category": "Dev / Assistant IA", "desc": "Assistant de programmation en binôme développé par GitHub et OpenAI."},
    
    # Modèles & LLMs
    "chatgpt": {"category": "IA / LLM", "desc": "Agent conversationnel et modèle de langage phare d'OpenAI."},
    "claude": {"category": "IA / LLM", "desc": "Modèle de langage développé par Anthropic, axé sur la sécurité et le code."},
    "gemini": {"category": "IA / Multimodal", "desc": "Modèle multimodal avancé développé par Google DeepMind."},
    "deepseek": {"category": "IA / LLM", "desc": "Modèles de langage et de raisonnement open-weights très performants."},
    "mistral": {"category": "IA / Open-Source", "desc": "Modèles de fondation haute performance développés par Mistral AI."},
    "llama": {"category": "IA / Open-Source", "desc": "Famille de modèles de langage open-source conçus par Meta."},
    "ollama": {"category": "IA / Local Runner", "desc": "Outil pour exécuter des modèles de langage localement en toute simplicité."},

    # Frameworks IA & Agents
    "langchain": {"category": "IA / Orchestration", "desc": "Framework modulaire pour développer des applications basées sur des LLMs."},
    "llamaindex": {"category": "IA / RAG", "desc": "Framework d'ingénierie de données pour connecter les LLMs aux données privées."},
    "crewai": {"category": "IA / Multi-Agents", "desc": "Framework d'orchestration pour faire collaborer des équipes d'agents IA."},
    "autogen": {"category": "IA / Multi-Agents", "desc": "Framework Microsoft pour les conversations multi-agents autonomes."},
    "hugging face": {"category": "IA / Hub & Models", "desc": "Plateforme centrale pour le partage de modèles, jeux de données et démos IA."},
    "transformers": {"category": "IA / Librairie", "desc": "Bibliothèque de référence pour manipuler les modèles de Deep Learning."},

    # Frameworks Web & Dev
    "next.js": {"category": "Dev / Framework Web", "desc": "Framework React pour le rendu hybride statique et côté serveur."},
    "react": {"category": "Dev / Librairie UI", "desc": "Bibliothèque JavaScript pour créer des interfaces utilisateur modulaires."},
    "vue": {"category": "Dev / Framework UI", "desc": "Framework JavaScript progressif pour construire des interfaces web."},
    "svelte": {"category": "Dev / Compilateur Web", "desc": "Compilateur frontend produisant du code ultra-performant sans Virtual DOM."},
    "fastapi": {"category": "Dev / Backend API", "desc": "Framework web Python moderne, ultra-rapide pour concevoir des APIs."},
    "flask": {"category": "Dev / Micro-Framework", "desc": "Micro-framework Python léger et flexible pour le web."},
    "django": {"category": "Dev / Framework Backend", "desc": "Framework web Python complet et robuste orienté batteries-included."},
    "tailwind": {"category": "Design / CSS", "desc": "Framework CSS utilitaire pour concevoir des designs modernes rapidement."},
    "shadcn/ui": {"category": "Design / Composants", "desc": "Composants d'interface React réutilisables et hautement personnalisables."},

    # Données, Backend & DevOps
    "supabase": {"category": "Dev / Backend-as-a-Service", "desc": "Alternative open-source à Firebase construite sur PostgreSQL."},
    "firebase": {"category": "Dev / BaaS", "desc": "Plateforme tout-en-un de Google pour le développement mobile et web."},
    "docker": {"category": "DevOps / Conteneurs", "desc": "Plateforme de conteneurisation pour déployer des applications de façon reproductible."},
    "kubernetes": {"category": "DevOps / Orchestration", "desc": "Système open-source d'automatisation du déploiement et de la mise à l'échelle de conteneurs."},
    "postgresql": {"category": "Base de données", "desc": "Système de gestion de base de données relationnelle objet puissant et open-source."},
    "sqlite": {"category": "Base de données", "desc": "Moteur de base de données SQL léger et autonome embarqué dans un fichier."},
    "qdrant": {"category": "IA / Base Vectorielle", "desc": "Moteur de recherche vectorielle et base de données pour embeddings IA."},
    "chromadb": {"category": "IA / Base Vectorielle", "desc": "Base de données vectorielle open-source orientée simplicité pour l'IA."},
    "pinecone": {"category": "IA / Base Vectorielle", "desc": "Base de données vectorielle gérée dans le cloud optimisée pour le RAG."},

    # Création visuelle & Médias
    "midjourney": {"category": "IA / Génération Image", "desc": "Générateur d'images photoréalistes et artistiques par IA."},
    "comfyui": {"category": "IA / Node UI", "desc": "Interface basée sur des nœuds la plus puissante pour Stable Diffusion."},
    "figma": {"category": "Design / UI-UX", "desc": "Outil collaboratif en ligne leader pour le prototypage et l'UI/UX design."},
}


def _analyze_with_gemini(text: str, api_key: str) -> Optional[List[DiscoveredTool]]:
    """Tente une analyse sémantique approfondie via l'API Gemini si disponible."""
    try:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = (
            "Tu es un ingénieur expert tech. Analyse le texte suivant et extrait TOUS les outils tech, logiciels, "
            "frameworks, bibliothèques, modèles IA ou plateformes de développement mentionnés.\n"
            "Retourne UNIQUEMENT un JSON valide au format suivant sans fioritures ni markdown :\n"
            "[\n"
            "  {\"name\": \"NomOutil\", \"category\": \"IA, Dev, Design...\", \"description\": \"Description courte en 1 phrase.\"}\n"
            "]\n\n"
            f"Texte à analyser :\n{text[:12000]}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=payload, timeout=25)
        if resp.status_code == 200:
            result = resp.json()
            raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Nettoyage des balises markdown si présentes
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            parsed = json.loads(raw_text.strip())
            tools = []
            for item in parsed:
                if item.get("name"):
                    tools.append(DiscoveredTool(
                        name=item["name"].strip(),
                        category=item.get("category", "Tech"),
                        description=item.get("description", "")
                    ))
            if tools:
                return tools
    except Exception as e:
        print(f"[Analyseur LLM] Repli sur l'analyseur local heuristique ({e})")
    return None


def _analyze_heuristic(text: str) -> List[DiscoveredTool]:
    """
    Analyse heuristique ultra-robuste basée sur le catalogue tech et les expressions régulières.
    Ne nécessite aucune clé API.
    """
    found_names = set()
    tools: List[DiscoveredTool] = []
    lower_text = text.lower()

    # 1. Correspondance avec le catalogue de référence
    for tech_name, data in KNOWN_TECH_CATALOG.items():
        pattern = r"\b" + re.escape(tech_name) + r"\b"
        if re.search(pattern, lower_text):
            # Préserver la casse propre
            display_name = tech_name.title()
            if tech_name in ["next.js", "bolt.new", "shadcn/ui", "comfyui"]:
                display_name = tech_name
            elif tech_name in ["chatgpt", "fastapi", "vue", "docker", "figma", "replit"]:
                display_name = tech_name.capitalize()
            elif tech_name in ["v0", "sqlite", "ide"]:
                display_name = tech_name

            found_names.add(tech_name)
            tools.append(DiscoveredTool(
                name=display_name,
                category=data["category"],
                description=data["desc"]
            ))

    # 2. Détection par expressions régulières pour capter d'autres outils non listés
    # Exemple : "l'outil SuperTool", "la librairie AwesomeLib", "le framework ReactQuery"
    patterns = [
        r"(?:outil|logiciel|framework|librairie|bibliothèque|agent|plateforme|modèle)\s+([A-Z][a-zA-Z0-9_\-\.]{2,20})",
        r"([A-Z][a-zA-Z0-9_\-\.]{2,20})\s+(?:framework|library|tool|sdk|api|agent)",
    ]
    for pat in patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            candidate = match.group(1).strip()
            cand_lower = candidate.lower()
            if cand_lower not in found_names and len(candidate) > 2:
                # Filtrer les mots communs en français ou anglais
                blacklist = {"cette", "notre", "votre", "dans", "pour", "avec", "cette", "sans", "comme", "leur", "this", "that", "with", "from"}
                if cand_lower not in blacklist:
                    found_names.add(cand_lower)
                    tools.append(DiscoveredTool(
                        name=candidate,
                        category="Tech / Découverte",
                        description=f"Outil technologique mentionné dans la ressource."
                    ))

    return tools


def scan_for_tools(text: str) -> List[DiscoveredTool]:
    """
    Point d'entrée unique pour l'Étape 2 :
    Scanne le texte et retourne la liste des outils technologiques détectés.
    """
    # 1. Vérifier si une clé Gemini est disponible dans l'environnement
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        llm_tools = _analyze_with_gemini(text, gemini_key)
        if llm_tools:
            return llm_tools

    # 2. Sinon, utiliser l'analyseur heuristique instantané
    return _analyze_heuristic(text)
