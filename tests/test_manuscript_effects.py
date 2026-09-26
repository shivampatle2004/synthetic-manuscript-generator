"""Unit tests for physical ManuscriptEffects pipeline."""

from pathlib import Path
import numpy as np
import pytest
from PIL import Image, ImageDraw

from src.config.settings import EffectsConfig, PageConfig
from src.effects.manuscript_effects import ManuscriptEffects
from src.pagination.page_builder import PageContent
from src.rendering.text_renderer import ManuscriptRenderer


def create_sample_manuscript_image(
    width: int = 600, height: int = 400
) -> Image.Image:
    """Create a test canvas simulating parchment with dark ink strokes."""
    img = Image.new("RGB", (width, height), color=(245, 238, 222))
    draw = ImageDraw.Draw(img)
    # Draw sample text and strokes
    draw.text((80, 60), "ॐ श्री गणेशाय नमः", fill=(40, 30, 25))
    draw.line([(80, 100), (300, 100)], fill=(40, 30, 25), width=3)
    return img


def test_effects_dimensions_and_mode_preserved() -> None:
    """Verify that applying effects preserves exact image dimensions and RGB mode."""
    img = create_sample_manuscript_image(800, 500)
    effects = ManuscriptEffects()
    result = effects.apply(img)

    assert isinstance(result, Image.Image)
    assert result.size == (800, 500)
    assert result.mode == "RGB"


def test_effects_deterministic_with_same_seed() -> None:
    """Verify that identical seeds produce bit-identical effect results."""
    img = create_sample_manuscript_image(400, 300)
    effects = ManuscriptEffects(config=EffectsConfig(seed=42))

    res1 = effects.apply(img, seed=42)
    res2 = effects.apply(img, seed=42)

    assert np.array_equal(np.array(res1), np.array(res2))


def test_effects_differ_with_different_seeds() -> None:
    """Verify that different seeds produce unique physical variations."""
    img = create_sample_manuscript_image(400, 300)
    effects = ManuscriptEffects()

    res1 = effects.apply(img, seed=10)
    res2 = effects.apply(img, seed=99)

    assert not np.array_equal(np.array(res1), np.array(res2))


def test_effects_disabled_leaves_image_unmodified() -> None:
    """Verify that disabled effects return the exact original image."""
    img = create_sample_manuscript_image(300, 200)
    effects = ManuscriptEffects(config=EffectsConfig(enabled=False))

    result = effects.apply(img)
    assert np.array_equal(np.array(img), np.array(result))


def test_each_effect_can_be_isolated() -> None:
    """Test that each physical effect can be enabled independently."""
    img = create_sample_manuscript_image(400, 300)

    # 1. Warp only
    warp_effects = ManuscriptEffects(
        config=EffectsConfig(
            enable_warp=True,
            enable_folds=False,
            enable_ink_bleed=False,
            enable_fade=False,
            enable_smudge=False,
            edge_wear_strength=0.0,
            seed=42,
        )
    )
    res_warp = warp_effects.apply(img)
    assert res_warp.size == img.size
    assert not np.array_equal(np.array(img), np.array(res_warp))

    # 2. Folds only
    fold_effects = ManuscriptEffects(
        config=EffectsConfig(
            enable_warp=False,
            enable_folds=True,
            fold_count=2,
            enable_ink_bleed=False,
            enable_fade=False,
            enable_smudge=False,
            edge_wear_strength=0.0,
            seed=42,
        )
    )
    res_folds = fold_effects.apply(img)
    assert res_folds.size == img.size
    assert not np.array_equal(np.array(img), np.array(res_folds))

    # 3. Ink bleed only
    bleed_effects = ManuscriptEffects(
        config=EffectsConfig(
            enable_warp=False,
            enable_folds=False,
            enable_ink_bleed=True,
            enable_fade=False,
            enable_smudge=False,
            edge_wear_strength=0.0,
            seed=42,
        )
    )
    res_bleed = bleed_effects.apply(img)
    assert res_bleed.size == img.size
    assert not np.array_equal(np.array(img), np.array(res_bleed))


def test_effects_config_validation() -> None:
    """Test validation of effect strengths and fold count bounds."""
    with pytest.raises(ValueError, match="fold_count cannot be negative"):
        EffectsConfig(fold_count=-1)

    with pytest.raises(ValueError, match="warp_strength must be between"):
        EffectsConfig(warp_strength=3.0)

    with pytest.raises(ValueError, match="ink_bleed_strength must be between"):
        EffectsConfig(ink_bleed_strength=-0.5)


def test_renderer_pipeline_integrates_effects(tmp_path: Path) -> None:
    """Verify that ManuscriptRenderer executes the effects layer end-to-end."""
    page_config = PageConfig(
        page_width=600,
        page_height=400,
        effects=EffectsConfig(enabled=True, seed=42),
    )
    renderer = ManuscriptRenderer(config=page_config)

    page = PageContent(
        page_number=1,
        text="अथ प्रथमोऽध्यायः",
        lines=["अथ प्रथमोऽध्यायः"],
        paragraphs=["अथ प्रथमोऽध्यायः"],
        line_count=1,
        usable_width=page_config.usable_width,
        usable_height=page_config.usable_height,
    )

    out_file = tmp_path / "effect_test.png"
    renderer.render_page(page, out_file)

    assert out_file.exists()
    with Image.open(out_file) as img:
        assert img.size == (600, 400)
        assert img.format == "PNG"
