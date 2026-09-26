"""Unit tests for PageBuilder pagination and geometry calculations."""

from pathlib import Path
import pytest

from src.config.settings import PageConfig
from src.input.manuscript_loader import Manuscript
from src.pagination.page_builder import PageBuilder, PageContent


def create_manuscript(paragraphs: list[str]) -> Manuscript:
    """Helper fixture to create in-memory Manuscript instances."""
    raw = "\n\n".join(paragraphs)
    return Manuscript(source_path=Path("test.md"), raw_text=raw, paragraphs=paragraphs)


def test_empty_manuscript_returns_no_pages() -> None:
    """Test that an empty manuscript returns an empty list of pages."""
    manuscript = create_manuscript([])
    builder = PageBuilder()
    pages = builder.paginate(manuscript)
    assert pages == []


def test_short_manuscript_single_page() -> None:
    """Test that a short manuscript fits onto a single page."""
    manuscript = create_manuscript(["Short manuscript text that easily fits on one page."])
    builder = PageBuilder()
    pages = builder.paginate(manuscript)

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert pages[0].line_count > 0
    assert "Short manuscript text" in pages[0].text
    assert pages[0].usable_width == builder.config.usable_width
    assert pages[0].usable_height == builder.config.usable_height


def test_long_manuscript_multiple_pages() -> None:
    """Test that long text spanning many paragraphs/lines divides into multiple pages."""
    paragraphs = [
        f"This is paragraph {i}. It contains multiple sentences to generate realistic manuscript content. "
        f"Historical documents often span multiple pages when transcribed."
        for i in range(40)
    ]
    manuscript = create_manuscript(paragraphs)
    builder = PageBuilder()
    pages = builder.paginate(manuscript)

    assert len(pages) > 1
    for idx, page in enumerate(pages):
        assert page.page_number == idx + 1
        assert page.line_count > 0
        assert len(page.lines) == page.line_count


def test_long_lines_wrap_within_usable_width() -> None:
    """Test that long lines wrap into multiple sublines, none exceeding usable width."""
    config = PageConfig(page_width=600, margin_left=50, margin_right=50)
    builder = PageBuilder(config=config)

    long_line = "शब्द " * 100
    manuscript = create_manuscript([long_line])
    pages = builder.paginate(manuscript)

    assert len(pages) >= 1
    for page in pages:
        for line in page.lines:
            assert builder.measure_text_width(line) <= config.usable_width


def test_very_long_unbroken_word_wraps_without_overflow() -> None:
    """Test that a continuous unbroken word longer than usable width is split safely."""
    config = PageConfig(page_width=400, margin_left=50, margin_right=50)
    builder = PageBuilder(config=config)

    unbroken_word = "अ" * 200
    manuscript = create_manuscript([unbroken_word])
    pages = builder.paginate(manuscript)

    assert len(pages) >= 1
    # Check that each line fits within usable width
    for page in pages:
        for line in page.lines:
            assert builder.measure_text_width(line) <= config.usable_width

    # Verify that all characters are preserved
    reconstructed = "".join(line for page in pages for line in page.lines)
    assert reconstructed == unbroken_word


def test_page_content_does_not_exceed_usable_height() -> None:
    """Test that accumulated line and paragraph heights never exceed usable height."""
    config = PageConfig(page_height=600, margin_top=50, margin_bottom=50, line_spacing=1.5)
    builder = PageBuilder(config=config)

    paragraphs = [f"Paragraph line sequence {i}" for i in range(60)]
    manuscript = create_manuscript(paragraphs)
    pages = builder.paginate(manuscript)

    assert len(pages) > 1
    line_h = builder.line_height

    for page in pages:
        # Number of lines * line height must strictly not exceed usable height
        total_line_height = page.line_count * line_h
        assert total_line_height <= config.usable_height


def test_manuscript_content_preserved_across_pages() -> None:
    """Test that pagination preserves all words and characters without silent drops."""
    paragraphs = [
        "प्रथमः परिच्छेदः । अयं ग्रन्थः ऐतिहासिकपाण्डुलिपिनां कृते अस्ति ।",
        "द्वितीयः परिच्छेदः । मोडी शारदा च देवनागरी लिपीनां समन्वयः अत्र वर्तते ।",
        "तृतीयः परिच्छेदः । सर्वे शब्दाः सुरक्षिताः स्युः ।",
    ]
    manuscript = create_manuscript(paragraphs)
    builder = PageBuilder()
    pages = builder.paginate(manuscript)

    # Collect all words from the original manuscript
    original_words = [word for p in paragraphs for word in p.split()]

    # Collect all words across all paginated pages
    paginated_words = [word for page in pages for line in page.lines for word in line.split()]

    assert paginated_words == original_words


def test_paragraph_boundaries_preserved() -> None:
    """Test that paragraph structure is respected across pages."""
    p1 = "Paragraph 1 first line.\nParagraph 1 second line."
    p2 = "Paragraph 2 content."
    p3 = "Paragraph 3 content."
    manuscript = create_manuscript([p1, p2, p3])

    builder = PageBuilder()
    pages = builder.paginate(manuscript)

    assert len(pages) >= 1
    # Check that p1, p2, and p3 are reflected in page paragraphs
    all_page_paragraphs = [para for page in pages for para in page.paragraphs]
    assert len(all_page_paragraphs) >= 3


def test_pagination_driven_by_geometry_not_fixed_lines() -> None:
    """Verify pagination changes dynamically based on page dimensions, not fixed line counts."""
    text = "Short line of text.\n" * 30
    manuscript = create_manuscript([text])

    # Small page height: fits fewer lines per page -> more pages
    small_config = PageConfig(page_height=300, font_size=24)
    small_builder = PageBuilder(config=small_config)
    pages_small = small_builder.paginate(manuscript)

    # Large page height: fits more lines per page -> fewer pages
    large_config = PageConfig(page_height=1400, font_size=24)
    large_builder = PageBuilder(config=large_config)
    pages_large = large_builder.paginate(manuscript)

    assert len(pages_small) > len(pages_large)
