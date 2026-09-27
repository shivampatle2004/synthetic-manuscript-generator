"""Unit tests for ManuscriptRenderer and text rendering pipeline."""

from pathlib import Path
import numpy as np
import pytest
from PIL import Image

from src.config.settings import BackgroundConfig, EffectsConfig, PageConfig
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


def test_scribal_variation_deterministic(tmp_path: Path) -> None:
    """Test that scribal line variation is 100% deterministic when seed is fixed."""
    text = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥"
    page = create_sample_page(page_number=1, text=text)

    cfg = PageConfig(
        background=BackgroundConfig(seed=42, texture_strength=0.0, aging_strength=0.0, stain_strength=0.0),
        effects=EffectsConfig(enabled=False, enable_scribal_variation=True, scribal_variation_strength=0.8, seed=100),
    )

    renderer1 = ManuscriptRenderer(config=cfg)
    target1 = tmp_path / "scribal_1.png"
    renderer1.render_page(page, target1)

    renderer2 = ManuscriptRenderer(config=cfg)
    target2 = tmp_path / "scribal_2.png"
    renderer2.render_page(page, target2)

    arr1 = np.array(Image.open(target1))
    arr2 = np.array(Image.open(target2))
    assert np.array_equal(arr1, arr2), "Scribal variation was not deterministic across identical seeds!"


def test_scribal_variation_zero_or_disabled(tmp_path: Path) -> None:
    """Test that disabled scribal variation or zero strength produces standard straight rendering."""
    text = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥"
    page = create_sample_page(page_number=1, text=text)

    cfg_disabled = PageConfig(
        background=BackgroundConfig(seed=42, texture_strength=0.0, aging_strength=0.0, stain_strength=0.0),
        effects=EffectsConfig(enabled=False, enable_scribal_variation=False, scribal_variation_strength=0.0),
    )
    renderer_disabled = ManuscriptRenderer(config=cfg_disabled)
    target_disabled = tmp_path / "disabled.png"
    renderer_disabled.render_page(page, target_disabled)

    cfg_zero_str = PageConfig(
        background=BackgroundConfig(seed=42, texture_strength=0.0, aging_strength=0.0, stain_strength=0.0),
        effects=EffectsConfig(enabled=False, enable_scribal_variation=True, scribal_variation_strength=0.0),
    )
    renderer_zero_str = ManuscriptRenderer(config=cfg_zero_str)
    target_zero_str = tmp_path / "zero_str.png"
    renderer_zero_str.render_page(page, target_zero_str)

    arr1 = np.array(Image.open(target_disabled))
    arr2 = np.array(Image.open(target_zero_str))
    assert np.array_equal(arr1, arr2), "Zero strength did not match disabled scribal variation!"


def test_scribal_variation_preserves_dimensions_and_shifts_organically(tmp_path: Path) -> None:
    """Test that scribal variation preserves page canvas dimensions while subtly undulating text strokes."""
    text = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥"
    page = create_sample_page(page_number=1, text=text)

    cfg_straight = PageConfig(
        background=BackgroundConfig(seed=42, texture_strength=0.0, aging_strength=0.0, stain_strength=0.0),
        effects=EffectsConfig(enabled=False, enable_scribal_variation=False),
    )
    renderer_straight = ManuscriptRenderer(config=cfg_straight)
    target_straight = tmp_path / "straight.png"
    renderer_straight.render_page(page, target_straight)

    cfg_scribal = PageConfig(
        background=BackgroundConfig(seed=42, texture_strength=0.0, aging_strength=0.0, stain_strength=0.0),
        effects=EffectsConfig(enabled=False, enable_scribal_variation=True, scribal_variation_strength=0.8, seed=42),
    )
    renderer_scribal = ManuscriptRenderer(config=cfg_scribal)
    target_scribal = tmp_path / "scribal.png"
    renderer_scribal.render_page(page, target_scribal)

    with Image.open(target_scribal) as img_scribal:
        assert img_scribal.size == (cfg_scribal.page_width, cfg_scribal.page_height)
        assert img_scribal.format == "PNG"

    arr_straight = np.array(Image.open(target_straight))
    arr_scribal = np.array(Image.open(target_scribal))

    # There should be subtle organic pixel differences in the text glyphs
    diff = np.abs(arr_straight.astype(int) - arr_scribal.astype(int))
    diff_pixels = np.sum(diff > 0)
    assert diff_pixels > 0, "Scribal variation produced no change compared to straight rendering!"


