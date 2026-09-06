"""
Module d'extraction : gère le parsing des pages web et la transcription YouTube.
Conçu de manière ultra-claire et robuste pour l'apprentissage et le Vibe Coding.
"""

import re
import urllib.parse
from dataclasses import dataclass
from typing import Optional
import requests
from bs4 import BeautifulSoup
from tech_scout.config import DEFAULT_HEADERS, REQUEST_TIMEOUT


@dataclass
class ExtractedContent:
    """Structure de données contenant le résultat de l'étape d'extraction."""
    source_url: str
    content_type: str  # 'youtube' ou 'webpage'
    title: str
    text: str


def is_youtube_url(url: str) -> bool:
    """Détecte si l'URL fournie correspond à une vidéo YouTube."""
    netloc = urllib.parse.urlparse(url).netloc.lower()
    return "youtube.com" in netloc or "youtu.be" in netloc


def extract_youtube_video_id(url: str) -> Optional[str]:
    """
    Extrait l'ID de la vidéo YouTube depuis différents formats d'URL :
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    """
    parsed = urllib.parse.urlparse(url)
    if "youtu.be" in parsed.netloc:
        return parsed.path.lstrip("/").split("?")[0]
    if "youtube.com" in parsed.netloc:
        if parsed.path == "/watch":
            queries = urllib.parse.parse_qs(parsed.query)
            return queries.get("v", [None])[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/shorts/")[1].split("/")[0]
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/embed/")[1].split("/")[0]
    # Fallback regex
    match = re.search(r"(?:v=|\/shorts\/|\/embed\/|youtu\.be\/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None


def fetch_youtube_transcript(url: str) -> ExtractedContent:
    """
    Récupère la transcription d'une vidéo YouTube via youtube-transcript-api.
    Supporte les transcriptions manuelles et auto-générées en FR ou EN.
    """
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

    video_id = extract_youtube_video_id(url)
    if not video_id:
        raise ValueError(f"Impossible d'extraire l'ID de la vidéo depuis l'URL : {url}")

    # Récupération du titre de la vidéo pour contextualiser
    title = f"YouTube Video ({video_id})"
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            if soup.title and soup.title.string:
                title = soup.title.string.replace(" - YouTube", "").strip()
    except Exception:
        pass

    # Récupération de la transcription
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Tentative 1 : chercher en français ou anglais (manuelle ou automatique)
        try:
            transcript = transcript_list.find_transcript(['fr', 'en', 'es', 'de'])
        except Exception:
            # Sinon prendre la première transcription disponible
            transcript = next(iter(transcript_list))
            
        data = transcript.fetch()
        full_text = " ".join([item.get("text", "") for item in data])
        # Nettoyage des retours à la ligne intempestifs
        full_text = re.sub(r"\s+", " ", full_text).strip()

        return ExtractedContent(
            source_url=url,
            content_type="youtube",
            title=title,
            text=full_text,
        )
    except (NoTranscriptFound, TranscriptsDisabled) as e:
        raise RuntimeError(f"Aucune transcription disponible pour cette vidéo : {e}")
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'extraction de la transcription YouTube : {e}")


def fetch_webpage_content(url: str) -> ExtractedContent:
    """
    Télécharge et extrait le texte d'un article de blog, thread ou page web.
    Nettoie les balises parasites (scripts, styles, pub, navigation).
    """
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Impossible d'accéder à l'URL ({url}) : {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Suppression des balises non pertinentes
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
        tag.decompose()

    # Titre de la page
    title = "Sans Titre"
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)

    # Extraction du corps de l'article prioritaire
    article = soup.find("article") or soup.find("main") or soup.find(class_=re.compile(r"content|post|article", re.I))
    target = article if article else soup.body or soup

    paragraphs = [p.get_text(" ", strip=True) for p in target.find_all(["p", "h1", "h2", "h3", "li"])]
    clean_text = "\n".join([p for p in paragraphs if len(p) > 15])

    if not clean_text:
        # Fallback si pas de paragraphes bien délimités
        clean_text = target.get_text(separator=" ", strip=True)

    # Normalisation des espaces
    clean_text = re.sub(r"[ \t]+", " ", clean_text)
    clean_text = re.sub(r"\n\s*\n+", "\n\n", clean_text).strip()

    return ExtractedContent(
        source_url=url,
        content_type="webpage",
        title=title,
        text=clean_text,
    )


def extract_content(url: str) -> ExtractedContent:
    """
    Point d'entrée unique pour l'Étape 1 :
    Analyse l'URL et aiguille automatiquement vers l'extracteur adapté.
    """
    clean_url = url.strip()
    if is_youtube_url(clean_url):
        return fetch_youtube_transcript(clean_url)
    return fetch_webpage_content(clean_url)
