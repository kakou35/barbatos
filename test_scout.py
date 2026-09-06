"""
Script de test unitaire et d'intégration pour l'agent Tech Scout.
Valide tous les modules sans dépendre d'une connexion internet externe si besoin.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from tech_scout.extractors import is_youtube_url, extract_youtube_video_id, ExtractedContent
from tech_scout.analyzer import scan_for_tools, DiscoveredTool
from tech_scout.browser_subagent import BrowserSubAgent, clean_url
from tech_scout.reporter import generate_markdown_report


def test_youtube_url_detection():
    print("Test 1 : Détection URL YouTube...")
    assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True
    assert is_youtube_url("https://example.com/blog") is False
    assert extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    print("✔ Détection YouTube validée !")


def test_analyzer_detection():
    print("\nTest 2 : Analyse et détection d'outils tech...")
    sample_text = (
        "Dans ce nouveau projet, nous utilisons Cursor comme IDE IA principal, avec Next.js pour le frontend "
        "et Tailwind pour le style. Pour la gestion des données, Supabase et PostgreSQL sont branchés sur Docker. "
        "Enfin, nous intégrons LangChain pour orchestrer des appels à Claude et Gemini."
    )
    tools = scan_for_tools(sample_text)
    names = [t.name.lower() for t in tools]
    print(f"Outils trouvés : {names}")
    for expected in ["cursor", "next.js", "tailwind", "supabase", "docker", "langchain", "claude", "gemini"]:
        assert expected in names, f"Outil manquant : {expected}"
    print("✔ Détection d'outils validée !")


def test_browser_subagent_resolution():
    print("\nTest 3 : Résolution d'URLs par le Browser Sub-agent...")
    browser = BrowserSubAgent(verbose=False)
    tool = DiscoveredTool(name="Cursor")
    enriched = browser.enrich_tool(tool)
    print(f"Cursor URL résolue : {enriched.official_url}")
    assert "cursor.com" in enriched.official_url
    assert clean_url("https://example.com/tool?utm_source=twitter&ref=123") == "https://example.com/tool"
    print("✔ Résolution et nettoyage d'URLs validés !")


def test_reporter_markdown():
    print("\nTest 4 : Génération de l'Artifact Markdown...")
    content = ExtractedContent(
        source_url="https://test.local/article",
        content_type="webpage",
        title="Article de Test Vibe Coding",
        text="Contenu de test"
    )
    tools = [
        DiscoveredTool(name="Cursor", category="Dev / IDE IA", description="IDE IA puissant.", official_url="https://www.cursor.com"),
        DiscoveredTool(name="Supabase", category="Dev / BaaS", description="Alternative Firebase open source.", official_url="https://supabase.com")
    ]
    report_file = "test_report.md"
    path = generate_markdown_report(content, tools, output_filename=report_file)
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        md = f.read()
    assert "| Nom de l'Outil | Catégorie (IA, Dev, Design...) | Description Rapide (1 phrase) | Lien Officiel |" in md
    assert "**Cursor**" in md
    assert "[Cursor](https://www.cursor.com)" in md
    os.remove(path)
    print("✔ Génération de l'Artifact Markdown validée !")


if __name__ == "__main__":
    test_youtube_url_detection()
    test_analyzer_detection()
    test_browser_subagent_resolution()
    test_reporter_markdown()
    print("\n🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
