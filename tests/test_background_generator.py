"""Unit tests for procedural BackgroundGenerator."""

import numpy as np
import pytest
from PIL import Image

from src.background.background_generator import BackgroundGenerator
from src.config.settings import BackgroundConfig, PageConfig
from src.pagination.page_builder import PageContent
from src.rendering.text_renderer import ManuscriptRenderer


def test_paper_background_generation() -> None:
    """Test paper background generates valid RGB image with correct dimensions."""
    config = BackgroundConfig(background_type="paper")
    generator = BackgroundGenerator(config=config, width=800, height=500)
    img = generator.generate()

    assert isinstance(img, Image.Image)
    assert img.size == (800, 500)
    assert img.mode == "RGB"


def test_palm_leaf_background_generation() -> None:
    """Test palm-leaf background generates valid RGB image with correct dimensions."""
    config = BackgroundConfig(background_type="palm_leaf")
    generator = BackgroundGenerator(config=config, width=1000, height=400)
    img = generator.generate()

    assert isinstance(img, Image.Image)
    assert img.size == (1000, 400)
    assert img.mode == "RGB"


def test_paper_and_palm_leaf_differ_substantially() -> None:
    """Verify that paper and palm-leaf produce distinctly different color and texture profiles."""
    gen_paper = BackgroundGenerator(
        config=BackgroundConfig(background_type="paper", seed=42),
        width=400,
        height=300,
    )
    gen_palm = BackgroundGenerator(
        config=BackgroundConfig(background_type="palm_leaf", seed=42),
        width=400,
        height=300,
    )

    arr_paper = np.array(gen_paper.generate())
    arr_palm = np.array(gen_palm.generate())

    # They should not be identical
    assert not np.array_equal(arr_paper, arr_palm)

    # Palm leaf is historically deeper golden-amber compared to antique paper
    mean_paper = arr_paper.mean(axis=(0, 1))
    mean_palm = arr_palm.mean(axis=(0, 1))
    # Paper is generally lighter overall than palm leaf
    assert mean_paper.mean() > mean_palm.mean()


def test_deterministic_output_with_identical_seed() -> None:
    """Verify that the same configuration and seed produce 100% identical pixel arrays."""
    config_a = BackgroundConfig(background_type="paper", seed=123)
    config_b = BackgroundConfig(background_type="paper", seed=123)

    gen_a = BackgroundGenerator(config=config_a, width=300, height=200)
    gen_b = BackgroundGenerator(config=config_b, width=300, height=200)

    img_a = gen_a.generate()
    img_b = gen_b.generate()

    arr_a = np.array(img_a)
    arr_b = np.array(img_b)

    assert np.array_equal(arr_a, arr_b)


def test_different_seeds_produce_different_backgrounds() -> None:
    """Verify that varying the seed creates subtle unique variations."""
    config_a = BackgroundConfig(background_type="paper", seed=42)
    config_b = BackgroundConfig(background_type="paper", seed=99)

    gen_a = BackgroundGenerator(config=config_a, width=300, height=200)
    gen_b = BackgroundGenerator(config=config_b, width=300, height=200)

    arr_a = np.array(gen_a.generate())
    arr_b = np.array(gen_b.generate())

    assert not np.array_equal(arr_a, arr_b)


def test_background_config_validation() -> None:
    """Test validation of background type and parameter bounds."""
    with pytest.raises(ValueError, match="Unknown background_type"):
        BackgroundConfig(background_type="unknown_material")

    with pytest.raises(ValueError, match="texture_strength must be between"):
        BackgroundConfig(texture_strength=-0.1)

    with pytest.raises(ValueError, match="aging_strength must be between"):
        BackgroundConfig(aging_strength=3.5)


def test_extensibility_material_registration() -> None:
    """Test registering a custom material generator for future extensibility."""
    generator = BackgroundGenerator(config=BackgroundConfig(background_type="paper"))

    def custom_generator(
        w: int, h: int, rng: np.random.Generator
    ) -> Image.Image:
        return Image.new("RGB", (w, h), color=(200, 200, 200))

    generator.register_material("custom_bark", custom_generator)
    generator.config.background_type = "custom_bark"

    custom_img = generator.generate(width=400, height=300)
    assert custom_img.size == (400, 300)
    assert custom_img.getpixel((0, 0)) == (200, 200, 200)


def test_renderer_successfully_uses_background_generator(tmp_path) -> None:
    """Verify that ManuscriptRenderer seamlessly uses BackgroundGenerator."""
    bg_config = BackgroundConfig(background_type="palm_leaf", seed=77)
    page_config = PageConfig(
        page_width=600,
        page_height=400,
        background=bg_config,
    )
    renderer = ManuscriptRenderer(config=page_config)

    page = PageContent(
        page_number=1,
        text="Sample line on palm leaf",
        lines=["Sample line on palm leaf"],
        paragraphs=["Sample line on palm leaf"],
        line_count=1,
        usable_width=page_config.usable_width,
        usable_height=page_config.usable_height,
    )

    out_file = tmp_path / "palm_test.png"
    renderer.render_page(page, out_file)

    assert out_file.exists()
    with Image.open(out_file) as img:
        assert img.size == (600, 400)
        assert img.format == "PNG"
