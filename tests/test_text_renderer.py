"""Unit tests for ManuscriptRenderer and text rendering pipeline."""

from pathlib import Path
import pytest
from PIL import Image

from src.config.settings import PageConfig
from src.pagination.page_builder import PageContent
from src.rendering.text_renderer import ManuscriptRenderer, find_default_indic_font


def create_sample_page(page_number: int = 1, text: str = "Test Line 1\nTest Line 2") -> PageContent:
    """Helper to create sample PageContent objects for testing."""
    lines = text.split("\n")
    return PageContent(
        page_number=page_number,
        text=text,
        lines=lines,
        paragraphs=[text],
        line_count=len(lines),
        usable_width=1040,
        usable_height=680,
    )


def test_renderer_creates_valid_png(tmp_path: Path) -> None:
    """Test that renderer produces an actual, valid PNG file."""
    renderer = ManuscriptRenderer()
    page = create_sample_page(page_number=1)
    target = tmp_path / "page_1.png"

    result_path = renderer.render_page(page, target)

    assert result_path.exists()
    assert result_path.is_file()
    assert result_path.stat().st_size > 0

    with Image.open(result_path) as img:
        assert img.format == "PNG"


def test_correct_image_dimensions(tmp_path: Path) -> None:
    """Test that the rendered image exactly matches configured page dimensions."""
    config = PageConfig(page_width=950, page_height=650)
    renderer = ManuscriptRenderer(config=config)
    page = create_sample_page()
    target = tmp_path / "dimension_test.png"

    renderer.render_page(page, target)

    with Image.open(target) as img:
        assert img.size == (950, 650)


def test_output_directory_creation(tmp_path: Path) -> None:
    """Test that nonexistent nested output directories are created automatically."""
    nested_dir = tmp_path / "sub1" / "sub2" / "images"
    target = nested_dir / "test.png"
    assert not nested_dir.exists()

    renderer = ManuscriptRenderer()
    page = create_sample_page()
    renderer.render_page(page, target)

    assert nested_dir.exists()
    assert target.exists()


def test_missing_font_raises_clear_error() -> None:
    """Test that configuring a non-existent font file raises FileNotFoundError with a clear message."""
    missing_path = "non_existent_path/fake_font.ttf"
    with pytest.raises(FileNotFoundError, match="Configured font file not found"):
        ManuscriptRenderer(font_path=missing_path)


def test_multiple_pages_rendered_sequentially(tmp_path: Path) -> None:
    """Test that multiple PageContent objects render with Image_001.png naming."""
    pages = [
        create_sample_page(page_number=1, text="Page 1 Content"),
        create_sample_page(page_number=2, text="Page 2 Content"),
        create_sample_page(page_number=3, text="Page 3 Content"),
    ]
    out_dir = tmp_path / "batch_out"

    renderer = ManuscriptRenderer()
    rendered = renderer.render_pages(pages, out_dir)

    assert len(rendered) == 3
    assert rendered[0].name == "Image_001.png"
    assert rendered[1].name == "Image_002.png"
    assert rendered[2].name == "Image_003.png"

    for path in rendered:
        assert path.exists()
        with Image.open(path) as img:
            assert img.format == "PNG"


def test_unicode_manuscript_text_rendering(tmp_path: Path) -> None:
    """Test rendering Unicode manuscript text with Indic characters."""
    indic_text = "ॐ श्री गणेशाय नमः ।\nअथ प्रथमोऽध्यायः ॥"
    page = create_sample_page(page_number=1, text=indic_text)
    target = tmp_path / "indic.png"

    # Use auto-discovered font or test-safe fallback
    renderer = ManuscriptRenderer()
    result = renderer.render_page(page, target)

    assert result.exists()
    with Image.open(result) as img:
        assert img.format == "PNG"
        assert img.size == (renderer.config.page_width, renderer.config.page_height)


def test_background_generator_modularity() -> None:
    """Test that create_page_background is modular and matches dimensions and color range."""
    renderer = ManuscriptRenderer(bg_color=(250, 245, 235))
    bg = renderer.create_page_background(800, 600)

    assert isinstance(bg, Image.Image)
    assert bg.size == (800, 600)
    # Check sample pixel is close to configured paper background color
    pixel = bg.getpixel((10, 10))
    assert abs(pixel[0] - 250) <= 20
    assert abs(pixel[1] - 245) <= 20
    assert abs(pixel[2] - 235) <= 20

