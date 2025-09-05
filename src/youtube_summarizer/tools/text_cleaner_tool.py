from crewai.tools import BaseTool
import re
from typing import Optional

class TranscriptCleanerTool(BaseTool):
    name: str = "Transcript Cleaner"
    description: str = "Cleans transcript text: removes timestamps and common fillers, normalizes whitespace. Preserves an optional metadata header at top."

    def _split_metadata(self, text: str) -> tuple[str, str]:
        """If there's a metadata header separated by a '---' line, split it out."""
        parts = text.split("\n---\n", 1)
        if len(parts) == 2:
            return parts[0].rstrip() + "\n\n---\n\n", parts[1]
        return "", text

    def _remove_timestamps(self, text: str) -> str:
        # Patterns like 00:00, 0:00:00, [00:00], (00:00)
        patterns = [
            r"\b\d{1,2}:\d{2}(?::\d{2})?\b",   # 0:00 or 00:00:00
            r"\[\d{1,2}:\d{2}(?::\d{2})?\]",  # [00:00]
            r"\(\d{1,2}:\d{2}(?::\d{2})?\)",  # (00:00)
        ]
        for p in patterns:
            text = re.sub(p, "", text)
        return text

    def _remove_fillers(self, text: str) -> str:
        # Basic filler words, non-destructive (word-boundary to avoid partial matches)
        fillers = [
            r"\bum\b", r"\buh\b", r"\blike\b", r"\byou know\b", r"\bsort of\b",
            r"\bkinda\b", r"\ber\b", r"\bem\b"
        ]
        for f in fillers:
            text = re.sub(f, "", text, flags=re.IGNORECASE)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        # Remove duplicate spaces and excessive newlines
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        # Restore line breaks at sentence boundaries heuristically (keep simple)
        text = re.sub(r"\.\s+", ".\n", text)
        return text.strip() + "\n"

    def _run(self, transcript_text: str) -> str:
        # Separate optional metadata header from body
        header, body = self._split_metadata(transcript_text)
        cleaned = self._remove_timestamps(body)
        cleaned = self._remove_fillers(cleaned)
        cleaned = self._normalize_whitespace(cleaned)
        return f"{header}{cleaned}"

