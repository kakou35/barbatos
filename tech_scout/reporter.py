"""
Module de rendu visuel et génération d'Artifact Markdown.
Génère le fichier 'tech_scout_report.md' sous un format propre, structuré et réutilisable.
"""

import os
from datetime import datetime
from typing import List
from tech_scout.analyzer import DiscoveredTool
from tech_scout.extractors import ExtractedContent
from tech_scout.config import DEFAULT_REPORT_FILENAME

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False


def generate_markdown_report(
    content: ExtractedContent,
    tools: List[DiscoveredTool],
    output_filename: str = DEFAULT_REPORT_FILENAME
) -> str:
    """
    Construit le rapport Markdown au format Artifact et l'enregistre sur le disque.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md_lines = [
        "# 🛠️ Tech Scout Report — Rapport de Veille Technologique",
        "",
        f"> **Généré le :** {now_str}  ",
        f"> **Source :** [{content.title}]({content.source_url})  ",
        f"> **Type de média :** `{content.content_type.upper()}`  ",
        f"> **Outils détectés & vérifiés :** `{len(tools)}`  ",
        "",
        "---",
        "",
        "## 📦 Synthèse des Outils et Technologies Détectés",
        "",
        "| Nom de l'Outil | Catégorie (IA, Dev, Design...) | Description Rapide (1 phrase) | Lien Officiel |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for tool in tools:
        # Lien cliquable propre
        link_md = f"[{tool.name}]({tool.official_url})" if tool.official_url else "N/A"
        # Échappement des pipes pour ne pas casser le tableau markdown
        safe_desc = tool.description.replace("|", "-")
        safe_cat = tool.category.replace("|", "/")
        md_lines.append(f"| **{tool.name}** | {safe_cat} | {safe_desc} | {link_md} |")

    md_lines.extend([
        "",
        "---",
        "",
        "### 💡 Conseils d'Utilisation (Vibe Coding)",
        "- Ce rapport a été généré de manière autonome par l'**Agent Tech Scout**.",
        "- Chaque lien a été vérifié et isolé de toute redirection publicitaire.",
        "- Vous pouvez copier ce tableau directement dans vos notes Notion, Obsidian ou dans vos documentations GitHub.",
        "",
        "*(Produit avec Google Antigravity & Vibe Coding Philosophy)*"
    ])

    report_content = "\n".join(md_lines)

    # Sauvegarde sur le disque local
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(report_content)

    return os.path.abspath(output_filename)


def display_final_results(tools: List[DiscoveredTool], report_path: str) -> None:
    """Affiche un rendu visuel du tableau final dans le terminal."""
    if HAS_RICH:
        table = Table(title="✨ Rapport Final Tech Scout (Extrait)", show_lines=True)
        table.add_column("Nom de l'Outil", style="bold green", min_width=15)
        table.add_column("Catégorie", style="magenta", min_width=18)
        table.add_column("Description Rapide", style="white", min_width=35)
        table.add_column("Lien Officiel", style="cyan", min_width=25)

        for tool in tools:
            table.add_row(
                tool.name,
                tool.category,
                tool.description,
                tool.official_url
            )

        console.print("\n")
        console.print(table)
        console.print(Panel(
            f"[bold green]✔ Rapport Artifact généré avec succès ![/bold green]\n"
            f"[bold white]Fichier :[/bold white] [cyan]{report_path}[/cyan]",
            title="📄 Artifact Markdown Prêt",
            border_style="green"
        ))
    else:
        print("\n" + "=" * 80)
        print("✨ RAPPORT FINAL TECH SCOUT")
        print("=" * 80)
        for tool in tools:
            print(f"- {tool.name} [{tool.category}] : {tool.official_url}")
            print(f"  {tool.description}")
        print("=" * 80)
        print(f"✔ Fichier généré : {report_path}\n")
