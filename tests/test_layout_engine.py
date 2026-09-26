"""Unit tests for LayoutEngine and manuscript page layout structures."""

from pathlib import Path
import pytest
from PIL import Image

from src.config.settings import LayoutConfig, PageConfig
from src.layout.layout_engine import (
    LayoutEngine,
    LayoutPage,
    SectionMarker,
    TextBlock,
    check_collision,
)
from src.pagination.page_builder import PageContent
from src.rendering.text_renderer import ManuscriptRenderer


def create_sample_page(page_number: int = 1) -> PageContent:
    """Helper to create sample PageContent."""
    lines = [
        "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।",
        "मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥",
        "दृष्ट्वा तु पाण्डवानीकं व्यूढं दुर्योधनस्तदा ।",
        "आचार्यमुपसङ्गम्य राजा वचनमब्रवीत् ॥",
    ]
    return PageContent(
        page_number=page_number,
        text="\n".join(lines),
        lines=lines,
        paragraphs=["\n".join(lines)],
        line_count=len(lines),
        usable_width=1040,
        usable_height=680,
    )


def test_traditional_single_layout() -> None:
    """Test traditional single-block layout structure."""
    engine = LayoutEngine()
    page = create_sample_page(page_number=1)
    cfg = LayoutConfig(layout_style="traditional_single", section_markers_enabled=True)

    layout = engine.build_layout(page, layout_config=cfg)

    assert isinstance(layout, LayoutPage)
    assert len(layout.blocks) == 1
    assert layout.blocks[0].role == "main_text"
    assert layout.blocks[0].lines == page.lines
    assert len(layout.markers) == 1
    assert layout.markers[0].marker_type == "lotus"


def test_multi_block_layout_preserves_text() -> None:
    """Test multi-block layout splits lines cleanly across blocks without text loss."""
    engine = LayoutEngine()
    page = create_sample_page(page_number=1)
    cfg = LayoutConfig(layout_style="multi_block")

    layout = engine.build_layout(page, layout_config=cfg)

    assert len(layout.blocks) == 2
    for b in layout.blocks:
        assert b.role == "main_text"

    # All lines from page must be preserved across blocks
    reconstructed_lines = layout.blocks[0].lines + layout.blocks[1].lines
    assert reconstructed_lines == page.lines

    # Section divider marker exists between blocks
    assert len(layout.markers) == 1
    assert layout.markers[0].marker_type == "danda_divider"
    assert layout.blocks[0].y < layout.markers[0].y < layout.blocks[1].y


def test_side_annotation_layout_and_no_collision() -> None:
    """Test side annotation layout has separate side column and no collision."""
    engine = LayoutEngine()
    page = create_sample_page(page_number=1)
    cfg = LayoutConfig(layout_style="side_annotation")
    page_cfg = PageConfig()

    layout = engine.build_layout(page, layout_config=cfg, page_config=page_cfg)

    assert len(layout.main_text_blocks) == 1
    assert len(layout.side_text_blocks) == 1

    main_block = layout.main_text_blocks[0]
    side_block = layout.side_text_blocks[0]

    # Verify no collision between main text and side commentary
    assert not check_collision(main_block.bounding_box, side_block.bounding_box)

    # Verify side block is inside page dimensions
    assert side_block.x + side_block.width <= page_cfg.page_width
    assert side_block.y + side_block.height <= page_cfg.page_height


def test_highlight_placement() -> None:
    """Test that enabling highlights marks the text block with historic pigment wash."""
    engine = LayoutEngine()
    page = create_sample_page(page_number=1)
    cfg = LayoutConfig(layout_style="traditional_single", highlights_enabled=True)

    layout = engine.build_layout(page, layout_config=cfg)

    assert layout.blocks[0].highlighted is True
    assert layout.blocks[0].highlight_color is not None


def test_collision_detection_logic() -> None:
    """Test collision checking function on overlapping and non-overlapping rectangles."""
    box1 = (10, 10, 50, 50)
    box2 = (40, 40, 80, 80)  # Overlaps box1
    box3 = (60, 60, 100, 100)  # Disjoint from box1

    assert check_collision(box1, box2) is True
    assert check_collision(box1, box3) is False


def test_boundary_validation_detects_overflow() -> None:
    """Test boundary validation catches out-of-bounds blocks."""
    engine = LayoutEngine()
    p_cfg = PageConfig(page_width=1000, page_height=600)

    # Create an invalid layout overflowing width
    overflow_block = TextBlock(
        block_id="invalid",
        text="Overflow",
        lines=["Overflow"],
        x=900,
        y=50,
        width=200,  # 900 + 200 = 1100 > 1000
        height=50,
    )
    bad_layout = LayoutPage(page_number=1, width=1000, height=600, blocks=[overflow_block])

    with pytest.raises(ValueError, match="exceeds page width"):
        engine._validate_boundaries(bad_layout, p_cfg)


def test_deterministic_layout_with_seed() -> None:
    """Verify identical layout seeds produce exact same coordinates."""
    engine = LayoutEngine()
    page = create_sample_page()
    cfg1 = LayoutConfig(layout_variation=0.5, seed=77)
    cfg2 = LayoutConfig(layout_variation=0.5, seed=77)

    layout1 = engine.build_layout(page, layout_config=cfg1)
    layout2 = engine.build_layout(page, layout_config=cfg2)

    assert layout1.blocks[0].x == layout2.blocks[0].x
    assert layout1.blocks[0].y == layout2.blocks[0].y


def test_renderer_integration_with_layout_page(tmp_path: Path) -> None:
    """Verify ManuscriptRenderer renders a LayoutPage to PNG end-to-end."""
    engine = LayoutEngine()
    page = create_sample_page(page_number=1)
    cfg = LayoutConfig(layout_style="side_annotation")
    page_cfg = PageConfig(page_width=800, page_height=500, layout=cfg)

    layout = engine.build_layout(page, layout_config=cfg, page_config=page_cfg)

    renderer = ManuscriptRenderer(config=page_cfg)
    target = tmp_path / "layout_rendered.png"

    result = renderer.render_page(layout, target)

    assert result.exists()
    with Image.open(result) as img:
        assert img.size == (800, 500)
        assert img.format == "PNG"
