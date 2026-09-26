"""Unit tests for AnnotationGenerator and ground-truth Markdown synchronization."""

from pathlib import Path
import pytest
from PIL import Image

from src.annotation.annotation_generator import AnnotationGenerator
from src.config.settings import LayoutConfig, PageConfig
from src.layout.layout_engine import (
    LayoutEngine,
    LayoutPage,
    SectionMarker,
    TextBlock,
)
from src.pagination.page_builder import PageContent
from src.rendering.text_renderer import ManuscriptRenderer


def create_sample_layout_page(
    page_number: int = 1,
    with_markers: bool = True,
    with_highlights: bool = False,
) -> LayoutPage:
    """Helper to construct sample LayoutPage."""
    text = "ॐ श्री गणेशाय नमः ।\nअथ प्रथमोऽध्यायः ॥"
    block = TextBlock(
        block_id=f"page_{page_number}_main",
        text=text,
        lines=text.split("\n"),
        x=80,
        y=60,
        width=1040,
        height=200,
        role="main_text",
        font_size=24,
        line_height=36,
        highlighted=with_highlights,
        highlight_color=(236, 188, 120) if with_highlights else None,
    )
    markers = (
        [SectionMarker(f"marker_{page_number}", "lotus", 570, 32, 60, 16)]
        if with_markers
        else []
    )
    return LayoutPage(
        page_number=page_number,
        width=1200,
        height=800,
        blocks=[block],
        markers=markers,
    )


def test_markdown_generation_structure() -> None:
    """Verify that generated Markdown contains all standardized sections."""
    gen = AnnotationGenerator(script="Devanagari", layout_style="traditional_single")
    page = create_sample_layout_page(1)
    md = gen.generate_markdown(page, image_filename="Image_001.png")

    assert "# Manuscript Page" in md
    assert "## Metadata" in md
    assert "- Image: Image_001.png" in md
    assert "- Page: 1" in md
    assert "- Script: Devanagari" in md
    assert "- Layout: traditional_single" in md
    assert "## Main Text" in md
    assert "## Blocks" in md
    assert "### Block: main_text" in md
    assert "## Section Markers" in md
    assert "## Highlights" in md


def test_utf8_and_devanagari_text_preservation(tmp_path: Path) -> None:
    """Verify that Devanagari and complex Indic script characters are preserved in UTF-8."""
    gen = AnnotationGenerator()
    page = create_sample_layout_page(1)
    out_file = tmp_path / "Image_001.md"

    gen.generate_annotation(page, out_file)
    content = out_file.read_text(encoding="utf-8")

    # Exact strings must be present without character corruption
    assert "ॐ श्री गणेशाय नमः ।" in content
    assert "अथ प्रथमोऽध्यायः ॥" in content


def test_block_metadata_inclusion() -> None:
    """Verify that block coordinates, dimensions, and typography metrics are documented."""
    gen = AnnotationGenerator()
    page = create_sample_layout_page(1)
    md = gen.generate_markdown(page)

    assert "- Block ID: page_1_main" in md
    assert "- Role: main_text" in md
    assert "- Position: x=80, y=60" in md
    assert "- Size: width=1040, height=200" in md
    assert "- Font Size: 24" in md
    assert "- Line Height: 36" in md
    assert "- Highlighted: false" in md


def test_side_text_metadata_inclusion() -> None:
    """Verify that secondary/commentary blocks in side_annotation layout are documented."""
    engine = LayoutEngine(config=LayoutConfig(layout_style="side_annotation"))
    p_content = PageContent(
        page_number=1,
        text="मूलग्रन्थस्य श्लोकः",
        lines=["मूलग्रन्थस्य श्लोकः"],
        paragraphs=["मूलग्रन्थस्य श्लोकः"],
        line_count=1,
        usable_width=1040,
        usable_height=680,
    )
    cfg = LayoutConfig(layout_style="side_annotation")
    layout = engine.build_layout(p_content, cfg, PageConfig(layout=cfg))

    gen = AnnotationGenerator(layout_style="side_annotation")
    md = gen.generate_markdown(layout)

    assert "### Block: main_text" in md
    assert "### Block: side_text" in md
    assert "मूलग्रन्थस्य श्लोकः" in md
    assert "॥ टीका ॥" in md


def test_marker_metadata_and_empty_handling() -> None:
    """Verify section marker documentation when present and 'None' when absent."""
    gen = AnnotationGenerator()

    # With markers
    page_with = create_sample_layout_page(1, with_markers=True)
    md_with = gen.generate_markdown(page_with)
    assert "- Marker ID: marker_1" in md_with
    assert "Type: lotus" in md_with
    assert "Position: x=570, y=32" in md_with

    # Without markers
    page_without = create_sample_layout_page(1, with_markers=False)
    md_without = gen.generate_markdown(page_without)
    assert "## Section Markers\n\nNone" in md_without


def test_highlight_metadata_and_empty_handling() -> None:
    """Verify highlight documentation when present and 'None' when absent."""
    gen = AnnotationGenerator()

    # With highlights
    page_high = create_sample_layout_page(1, with_highlights=True)
    md_high = gen.generate_markdown(page_high)
    assert "## Highlights\n\n- Block: page_1_main" in md_high
    assert "Role: main_text" in md_high

    # Without highlights
    page_none = create_sample_layout_page(1, with_highlights=False)
    md_none = gen.generate_markdown(page_none)
    assert "## Highlights\n\nNone" in md_none


def test_filename_synchronization() -> None:
    """Verify that annotation explicitly records the corresponding image filename."""
    gen = AnnotationGenerator()
    page = create_sample_layout_page(2)
    md = gen.generate_markdown(page, image_filename="Image_002.png")

    assert "- Image: Image_002.png" in md
    assert "- Page: 2" in md


def test_deterministic_annotation_output() -> None:
    """Verify identical layout inputs produce bit-identical Markdown output."""
    gen = AnnotationGenerator()
    page = create_sample_layout_page(1)

    md1 = gen.generate_markdown(page)
    md2 = gen.generate_markdown(page)

    assert md1 == md2


def test_end_to_end_png_and_md_synchronization(tmp_path: Path) -> None:
    """Test full end-to-end generation where LayoutPage produces paired PNG and MD files."""
    page_config = PageConfig()
    engine = LayoutEngine(config=page_config.layout)
    renderer = ManuscriptRenderer(config=page_config)
    annotator = AnnotationGenerator()

    page_content = PageContent(
        page_number=1,
        text="अथ प्रथमोऽध्यायः ॥",
        lines=["अथ प्रथमोऽध्यायः ॥"],
        paragraphs=["अथ प्रथमोऽध्यायः ॥"],
        line_count=1,
        usable_width=page_config.usable_width,
        usable_height=page_config.usable_height,
    )

    # Single source of truth: LayoutPage
    layout_page = engine.build_layout(page_content, page_config.layout, page_config)

    png_path = tmp_path / "Image_001.png"
    md_path = tmp_path / "Image_001.md"

    renderer.render_layout_page(layout_page, png_path)
    annotator.generate_annotation(layout_page, md_path, image_filename=png_path.name)

    # 1. Both files must exist
    assert png_path.exists()
    assert md_path.exists()

    # 2. PNG is valid image
    with Image.open(png_path) as img:
        assert img.size == (page_config.page_width, page_config.page_height)
        assert img.format == "PNG"

    # 3. MD contains exact text
    md_content = md_path.read_text(encoding="utf-8")
    assert "- Image: Image_001.png" in md_content
    assert "अथ प्रथमोऽध्यायः ॥" in md_content
