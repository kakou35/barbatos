#!/usr/bin/env python3
"""
=============================================================================
🤖 AGENT AUTONOME TECH SCOUT — VIBE CODING EDITION
=============================================================================
Cet agent autonome permet d'analyser n'importe quelle URL (article tech, thread,
vidéo YouTube), d'en extraire les outils et logiciels mentionnés, de rechercher
de manière autonome leurs sites officiels, et de produire un rapport Markdown
propre et structuré.

Sécurité :
Une politique de sécurité avec "Manager Surface" exige la validation d'un clic
avant de déclencher le sous-agent de navigation web.

Usage :
    python main.py
    python main.py --url https://www.youtube.com/watch?v=dQw4w9WgXcQ
    python main.py --url https://example.com/blog --auto-approve
=============================================================================
"""

import sys
import argparse

# Configuration UTF-8 robuste pour la console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from tech_scout.config import AgentConfig, DEFAULT_REPORT_FILENAME
from tech_scout.extractors import extract_content
from tech_scout.analyzer import scan_for_tools
from tech_scout.policy import request_manager_approval
from tech_scout.browser_subagent import BrowserSubAgent
from tech_scout.reporter import generate_markdown_report, display_final_results

try:
    from rich.console import Console
    from rich.panel import Panel
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False


def print_banner():
    """Affiche la bannière d'accueil de l'agent."""
    title = (
        "🚀 AGENT AUTONOME TECH SCOUT\n"
        "Veille Technologique & Navigation Autonome (Vibe Coding)"
    )
    if HAS_RICH:
        console.print(Panel(title, style="bold cyan", border_style="cyan"))
    else:
        print("=" * 70)
        print(title)
        print("=" * 70)


def run_agent(target_url: str, auto_approve: bool = False, output_file: str = DEFAULT_REPORT_FILENAME):
    """
    Orchestration complète du workflow de l'agent autonome :
    1. Extraction du contenu (Web ou YouTube)
    2. Analyse et détection des outils tech
    3. Point de contrôle Human-in-the-Loop (Manager Surface)
    4. Enrichissement via le Browser Sub-agent
    5. Génération de l'Artifact Markdown
    """
    print_banner()
    print(f"🎯 Cible initiale : {target_url}\n")

    # =========================================================================
    # ÉTAPE 1 : EXTRACTION DU CONTENU
    # =========================================================================
    print("⏳ [Étape 1/4] Extraction du contenu en cours...")
    try:
        content = extract_content(target_url)
        print(f"  ✔ Contenu extrait ({content.content_type.upper()}) : '{content.title}'")
        print(f"  ✔ Taille du texte analysable : {len(content.text)} caractères\n")
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction : {e}")
        sys.exit(1)

    # =========================================================================
    # ÉTAPE 2 : ANALYSE & DÉTECTION DES OUTILS
    # =========================================================================
    print("🧠 [Étape 2/4] Scan et identification des outils tech...")
    tools = scan_for_tools(content.text)
    if not tools:
        print("⚠️ Aucun outil ou framework tech n'a été détecté dans ce contenu.")
        print("💡 Essayez avec une URL traitant de développement ou d'intelligence artificielle.")
        sys.exit(0)
    print(f"  ✔ {len(tools)} technologie(s) identifiée(s) dans le texte !\n")

    # =========================================================================
    # HUMAN-IN-THE-LOOP : MANAGER SURFACE & VALIDATION SÉCURISÉE
    # =========================================================================
    # L'agent suspend son exécution pour obtenir le consentement de l'humain
    approved_tools = request_manager_approval(tools, target_url, auto_approve=auto_approve)

    # =========================================================================
    # ÉTAPE 3 : NAVIGATION AUTONOME (BROWSER SUB-AGENT)
    # =========================================================================
    print("🌐 [Étape 3/4] Lancement du Browser Sub-agent...")
    browser = BrowserSubAgent(verbose=True)
    enriched_tools = browser.run_enrichment(approved_tools)

    # =========================================================================
    # ÉTAPE 4 : RENDU VISUEL & ARTIFACT MARKDOWN
    # =========================================================================
    print("📄 [Étape 4/4] Création de l'Artifact Markdown...")
    report_path = generate_markdown_report(content, enriched_tools, output_file)
    display_final_results(enriched_tools, report_path)


def main():
    parser = argparse.ArgumentParser(
        description="Agent Autonome Tech Scout - Détecte et référence les outils tech depuis une URL."
    )
    parser.add_argument(
        "--url",
        type=str,
        help="L'URL à analyser (article de blog, thread ou lien YouTube)."
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Valide automatiquement l'étape de contrôle Manager Surface sans interaction."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_REPORT_FILENAME,
        help=f"Nom du fichier de rapport Markdown de sortie (défaut : {DEFAULT_REPORT_FILENAME})."
    )

    args = parser.parse_args()

    # Si aucune URL n'est passée en argument, demander interactivement
    url = args.url
    if not url:
        print_banner()
        try:
            url = input("👉 Entrez l'URL à analyser (Article tech ou lien YouTube) : ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSortie.")
            sys.exit(0)

    if not url:
        print("❌ Aucune URL fournie. Sortie du programme.")
        sys.exit(1)

    run_agent(target_url=url, auto_approve=args.auto_approve, output_file=args.output)


if __name__ == "__main__":
    main()
