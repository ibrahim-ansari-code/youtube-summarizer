from crewai.tools import BaseTool
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any, ClassVar, List
import logging
import requests

logger = logging.getLogger(__name__)

class EnhancedTranscriptTool(BaseTool):
    name: str = "youtube transcript extractor"
    description: str = "gets youtube video transcripts with language support"
    
    # languages in priority order
    LANGUAGE_PRIORITIES: ClassVar[List[str]] = [
        'en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'ru', 'ar', 'hi'
    ]

    def _get_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats."""
        try:
            query = urlparse(url)
            if query.hostname == 'youtu.be':
                return query.path[1:]
            elif query.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
                if 'v=' in query.query:
                    return parse_qs(query.query).get('v', [None])[0]
                elif '/embed/' in query.path:
                    return query.path.split('/embed/')[1].split('?')[0]
                elif '/watch/' in query.path:
                    return query.path.split('/watch/')[1]
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
        return None

    def _get_available_languages(self, video_id: str) -> Dict[str, Any]:
        """Get all available transcript languages for a video."""
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            languages: Dict[str, Any] = {}
            for transcript in transcript_list:
                languages[transcript.language_code] = {
                    'language': transcript.language,
                    'language_code': transcript.language_code,
                    'is_generated': transcript.is_generated,
                    'is_translatable': hasattr(transcript, 'is_translatable') and transcript.is_translatable
                }
            return languages
        except Exception as e:
            logger.error(f"Error getting available languages: {e}")
            return {}

    def _select_best_language(self, available_languages: Dict[str, Any], preferred_language: Optional[str] = None) -> Optional[str]:
        """Select the best available language based on preferences."""
        if not available_languages:
            return None
        if preferred_language:
            if preferred_language in available_languages:
                return preferred_language
            for lang_code in available_languages:
                if lang_code.startswith(preferred_language):
                    return lang_code
        for priority_lang in self.LANGUAGE_PRIORITIES:
            if priority_lang in available_languages:
                return priority_lang
            for lang_code in available_languages:
                if lang_code.startswith(priority_lang):
                    return lang_code
        return list(available_languages.keys())[0] if available_languages else None

    def _fetch_oembed_metadata(self, url: str) -> Dict[str, Any]:
        """Fetch basic metadata (title, author) using YouTube oEmbed (no API key)."""
        try:
            resp = requests.get(
                "https://www.youtube.com/oembed",
                params={"url": url, "format": "json"},
                timeout=8
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "title": data.get("title"),
                    "author": data.get("author_name"),
                    "provider": data.get("provider_name")
                }
        except Exception as e:
            logger.warning(f"oEmbed metadata fetch failed: {e}")
        return {"title": None, "author": None, "provider": None}

    def _run(self, url: str, language: Optional[str] = None) -> str:
        """Extract transcript with language support and prepend metadata header."""
        video_id = self._get_video_id(url)
        if not video_id:
            return "Error: Invalid YouTube URL format."

        try:
            # Get available languages
            available_languages = self._get_available_languages(video_id)
            if not available_languages:
                return "Error: No transcripts available for this video."
            
            # Select best language
            selected_language = self._select_best_language(available_languages, language)
            if not selected_language:
                return "Error: Could not find suitable transcript language."
            
            # Get transcript
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            transcript = None
            for t in transcript_list:
                if t.language_code == selected_language:
                    transcript = t
                    break
            
            if not transcript:
                return "Error: Could not find transcript for selected language."
            
            fetched = transcript.fetch()
            transcript_text = "\n".join([segment.text for segment in fetched])

            # oEmbed metadata
            meta = self._fetch_oembed_metadata(url)
            language_info = available_languages[selected_language]

            # Build metadata header
            metadata_lines = [
                "# Video Metadata",
                f"Title: {meta.get('title') or 'Unknown'}",
                f"Channel: {meta.get('author') or 'Unknown'}",
                f"URL: {url}",
                f"Video ID: {video_id}",
                f"Transcript Language: {language_info['language']} ({selected_language})",
                f"Auto-generated: {'Yes' if language_info['is_generated'] else 'No'}",
                "",
                "---",
                "",
            ]
            header = "\n".join(metadata_lines)
            return header + transcript_text
        except Exception as e:
            logger.error(f"Error extracting transcript: {e}")
            return f"Error extracting transcript: {str(e)}"
