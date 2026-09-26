"""Unit tests for PageConfig settings."""

import pytest

from src.config.settings import PageConfig


def test_default_page_config() -> None:
    """Test sensible defaults for PageConfig."""
    config = PageConfig()
    assert config.page_width == 1200
    assert config.page_height == 800
    assert config.usable_width == 1200 - 80 - 80
    assert config.usable_height == 800 - 60 - 60
    assert config.font_size == 24
    assert config.line_spacing == 1.5


def test_invalid_dimensions_raise_error() -> None:
    """Test that non-positive dimensions raise ValueError."""
    with pytest.raises(ValueError, match="Page dimensions must be positive"):
        PageConfig(page_width=0, page_height=800)

    with pytest.raises(ValueError, match="Margins cannot be negative"):
        PageConfig(margin_left=-10)


def test_excessive_margins_raise_error() -> None:
    """Test that margins exceeding page dimensions raise ValueError."""
    with pytest.raises(ValueError, match="Usable width.*must be positive"):
        PageConfig(page_width=100, margin_left=60, margin_right=50)

    with pytest.raises(ValueError, match="Usable height.*must be positive"):
        PageConfig(page_height=100, margin_top=60, margin_bottom=50)


def test_invalid_font_size_or_spacing() -> None:
    """Test that non-positive font size or line spacing raises ValueError."""
    with pytest.raises(ValueError, match="font_size must be positive"):
        PageConfig(font_size=0)

    with pytest.raises(ValueError, match="line_spacing must be positive"):
        PageConfig(line_spacing=-0.5)
