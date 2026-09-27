"""Intelligent page building and pagination based on geometry and typography."""

import math
from dataclasses import dataclass, field
from typing import List, Optional

from PIL import ImageFont

from src.config.settings import PageConfig
from src.input.manuscript_loader import Manuscript


@dataclass
class PageContent:
    """Structured representation of a single paginated manuscript page."""

    page_number: int
    text: str
    lines: List[str] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)
    line_count: int = 0
    usable_width: int = 0
    usable_height: int = 0

    @property
    def estimated_line_count(self) -> int:
        """Alias for line_count for backward and forward compatibility."""
        return self.line_count

    @property
    def character_count(self) -> int:
        """Total character count on this page."""
        return len(self.text)


class PageBuilder:
    """Paginates manuscripts intelligently based on page geometry and typography."""

    def __init__(self, config: Optional[PageConfig] = None) -> None:
        self.config = config or PageConfig()
        self.font = self._load_font()
        self.line_height = self._calculate_line_height()

    def _load_font(self) -> ImageFont.ImageFont:
        """Load configured TrueType font or fallback to Pillow's scalable default font."""
        if self.config.font_path:
            return ImageFont.truetype(self.config.font_path, size=self.config.font_size)
        try:
            return ImageFont.load_default(size=self.config.font_size)
        except TypeError:
            return ImageFont.load_default()

    def _calculate_line_height(self) -> int:
        """Calculate line height using font metrics and line spacing multiplier."""
        bbox = self.font.getbbox("Aygy|Éअक")
        char_height = (bbox[3] - bbox[1]) if bbox else self.config.font_size
        base_height = max(char_height, self.config.font_size)
        return max(1, int(math.ceil(base_height * self.config.line_spacing)))

    def measure_text_width(self, text: str) -> float:
        """Accurately measure text width using Pillow font metrics."""
        if not text:
            return 0.0
        if hasattr(self.font, "getlength"):
            return float(self.font.getlength(text))
        bbox = self.font.getbbox(text)
        return float(bbox[2] - bbox[0]) if bbox else 0.0

    def wrap_line(self, line: str, max_width: float) -> List[str]:
        """Wrap a single text line into multiple lines fitting within max_width.

        Preserves all words and characters. Handles very long unbroken words
        by splitting character-by-character to strictly prevent page boundary overflow.
        """
        stripped = line.strip()
        if not stripped:
            return []

        words = stripped.split(" ")
        lines: List[str] = []
        current_words: List[str] = []

        for word in words:
            if not word:
                continue

            test_line = " ".join(current_words + [word]) if current_words else word
            if self.measure_text_width(test_line) <= max_width:
                current_words.append(word)
            else:
                # Flush the current line
                if current_words:
                    lines.append(" ".join(current_words))
                    current_words = []

                # Handle words wider than the entire usable page width
                if self.measure_text_width(word) > max_width:
                    sub_chunk = ""
                    for char in word:
                        if self.measure_text_width(sub_chunk + char) <= max_width:
                            sub_chunk += char
                        else:
                            if sub_chunk:
                                lines.append(sub_chunk)
                            sub_chunk = char
                    if sub_chunk:
                        current_words.append(sub_chunk)
                else:
                    current_words.append(word)

        if current_words:
            lines.append(" ".join(current_words))

        return lines

    def wrap_paragraph(self, paragraph: str, max_width: float) -> List[str]:
        """Wrap an entire paragraph, respecting any explicit verse/newline breaks."""
        lines: List[str] = []
        for raw_line in paragraph.splitlines():
            wrapped = self.wrap_line(raw_line, max_width)
            lines.extend(wrapped)
        return lines

    def paginate(
        self, manuscript: Manuscript, max_pages: Optional[int] = None
    ) -> List[PageContent]:
        """Paginate a manuscript into structured PageContent objects.

        Pagination is strictly driven by geometry and typography:
        - Usable width and usable height are respected.
        - Long lines wrap to fit usable width.
        - Lines are accumulated until usable page height is reached.
        - Paragraph spacing is preserved where geometry permits.
        - No text or words are dropped across pages.
        - Optional max_pages stops early to avoid unnecessary processing on massive corpora.
        """
        if not manuscript.paragraphs:
            return []

        usable_w = self.config.usable_width
        usable_h = self.config.usable_height
        line_h = self.line_height
        paragraph_gap = int(self.config.paragraph_spacing * line_h)

        pages: List[PageContent] = []
        current_page_lines: List[str] = []
        current_page_paragraphs: List[List[str]] = []
        current_para_lines: List[str] = []
        current_height = 0
        page_number = 1

        def flush_page() -> None:
            nonlocal page_number, current_page_lines, current_page_paragraphs, current_para_lines, current_height
            if current_para_lines:
                current_page_paragraphs.append(list(current_para_lines))
                current_para_lines = []

            para_texts = ["\n".join(para) for para in current_page_paragraphs if para]
            page_text = "\n\n".join(para_texts)

            pages.append(
                PageContent(
                    page_number=page_number,
                    text=page_text,
                    lines=list(current_page_lines),
                    paragraphs=para_texts,
                    line_count=len(current_page_lines),
                    usable_width=usable_w,
                    usable_height=usable_h,
                )
            )
            page_number += 1
            current_page_lines = []
            current_page_paragraphs = []
            current_height = 0

        for para in manuscript.paragraphs:
            if max_pages is not None and len(pages) >= max_pages:
                break

            # If there are already lines on the page, account for paragraph spacing
            if current_page_lines:
                if current_height + paragraph_gap + line_h <= usable_h:
                    current_height += paragraph_gap
                    if current_para_lines:
                        current_page_paragraphs.append(list(current_para_lines))
                        current_para_lines = []
                else:
                    # Not enough room for paragraph gap + at least one line; advance page
                    flush_page()
                    if max_pages is not None and len(pages) >= max_pages:
                        break

            # Wrap line by line so massive paragraphs break early without measuring entire file
            for raw_line in para.splitlines():
                if max_pages is not None and len(pages) >= max_pages:
                    break
                wrapped_lines = self.wrap_line(raw_line, usable_w)
                for line in wrapped_lines:
                    if current_height + line_h > usable_h and current_page_lines:
                        flush_page()
                        if max_pages is not None and len(pages) >= max_pages:
                            break

                    current_page_lines.append(line)
                    current_para_lines.append(line)
                    current_height += line_h

            if current_para_lines:
                current_page_paragraphs.append(list(current_para_lines))
                current_para_lines = []

        if current_page_lines and (max_pages is None or len(pages) < max_pages):
            flush_page()

        if max_pages is not None:
            return pages[:max_pages]
        return pages
