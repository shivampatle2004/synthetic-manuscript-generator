"""Input processing and text ingestion module for manuscript files."""

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Union


@dataclass(frozen=True)
class Manuscript:
    """Structured representation of an ingested manuscript."""

    source_path: Path
    raw_text: str
    paragraphs: List[str] = field(default_factory=list)

    @property
    def character_count(self) -> int:
        """Total number of characters in the normalized text."""
        return len(self.raw_text)

    @property
    def word_count(self) -> int:
        """Total number of words across all paragraphs."""
        return sum(len(p.split()) for p in self.paragraphs)

    @property
    def paragraph_count(self) -> int:
        """Total number of preserved paragraphs."""
        return len(self.paragraphs)


class ManuscriptLoader:
    """Loads and safely normalizes manuscript markdown files."""

    @staticmethod
    def load(file_path: Union[str, Path]) -> Manuscript:
        """Load a markdown manuscript from disk with safe normalization.

        Performs only minimal, non-destructive normalization:
        1. Strips UTF-8 Byte Order Mark (BOM) if present.
        2. Normalizes CRLF and CR line endings to standard LF (\n).
        3. Applies Unicode NFC normalization to ensure canonical representation
           of complex Indic script character sequences and diacritics.
        4. Preserves paragraph boundaries and internal text formatting.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the path does not point to a regular file.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Manuscript file not found: {path.resolve()}")
        if not path.is_file():
            raise ValueError(f"Path is not a regular file: {path.resolve()}")

        content = path.read_text(encoding="utf-8")

        # 1. Strip UTF-8 BOM
        if content.startswith("\ufeff"):
            content = content[1:]

        # 2. Normalize CRLF and CR to LF
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # 3. Unicode NFC normalization (essential for Indic scripts like Devanagari, Modi, Sharada)
        content = unicodedata.normalize("NFC", content)

        # 4. Extract paragraphs separated by two or more newlines
        stripped = content.strip()
        if not stripped:
            paragraphs: List[str] = []
        else:
            raw_blocks = re.split(r"\n\s*\n+", content)
            paragraphs = [block.strip() for block in raw_blocks if block.strip()]

        return Manuscript(
            source_path=path,
            raw_text=content,
            paragraphs=paragraphs,
        )
