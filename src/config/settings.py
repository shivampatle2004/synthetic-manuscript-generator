"""Configuration settings for page geometry, typography, backgrounds, physical effects, and layout."""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from src.config.script_config import (
    DatasetConfig,
    ScriptConfig,
    get_default_scripts,
    resolve_script_font,
    resolve_script_input,
)


@dataclass
class BackgroundConfig:
    """Configuration settings for procedural historical manuscript backgrounds."""

    background_type: str = "paper"  # "paper" or "palm_leaf"
    texture_strength: float = 0.5
    aging_strength: float = 0.4
    stain_strength: float = 0.3
    edge_variation: float = 0.4
    seed: Optional[int] = None
    base_color: Optional[Tuple[int, int, int]] = None

    def __post_init__(self) -> None:
        valid_types = ("paper", "palm_leaf")
        if self.background_type not in valid_types:
            raise ValueError(
                f"Unknown background_type '{self.background_type}'. Supported: {valid_types}"
            )
        for name, val in [
            ("texture_strength", self.texture_strength),
            ("aging_strength", self.aging_strength),
            ("stain_strength", self.stain_strength),
            ("edge_variation", self.edge_variation),
        ]:
            if not 0.0 <= val <= 2.0:
                raise ValueError(f"{name} must be between 0.0 and 2.0, got {val}")


@dataclass
class EffectsConfig:
    """Configuration settings for physical manuscript imperfections and artifacts."""

    enabled: bool = True
    enable_warp: bool = True
    warp_strength: float = 0.3
    enable_folds: bool = True
    fold_strength: float = 0.3
    fold_count: int = 1
    enable_ink_bleed: bool = True
    ink_bleed_strength: float = 0.3
    enable_fade: bool = True
    fade_strength: float = 0.3
    enable_smudge: bool = True
    smudge_strength: float = 0.2
    edge_wear_strength: float = 0.3
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        if self.fold_count < 0:
            raise ValueError(f"fold_count cannot be negative, got {self.fold_count}")
        for name, val in [
            ("warp_strength", self.warp_strength),
            ("fold_strength", self.fold_strength),
            ("ink_bleed_strength", self.ink_bleed_strength),
            ("fade_strength", self.fade_strength),
            ("smudge_strength", self.smudge_strength),
            ("edge_wear_strength", self.edge_wear_strength),
        ]:
            if not 0.0 <= val <= 2.0:
                raise ValueError(f"{name} must be between 0.0 and 2.0, got {val}")


@dataclass
class LayoutConfig:
    """Configuration settings for manuscript page layout structures."""

    layout_style: str = "traditional_single"  # "traditional_single", "side_annotation", "multi_block"
    side_text_enabled: bool = False
    section_markers_enabled: bool = True
    highlights_enabled: bool = False
    layout_variation: float = 0.2
    seed: Optional[int] = None
    side_text_content: Optional[str] = None

    def __post_init__(self) -> None:
        valid_styles = ("traditional_single", "side_annotation", "multi_block")
        if self.layout_style not in valid_styles:
            raise ValueError(
                f"Unknown layout_style '{self.layout_style}'. Supported: {valid_styles}"
            )
        if not 0.0 <= self.layout_variation <= 1.0:
            raise ValueError(
                f"layout_variation must be between 0.0 and 1.0, got {self.layout_variation}"
            )


@dataclass
class PageConfig:
    """Configurable settings for page geometry, typography, and pagination."""

    page_width: int = 1200
    page_height: int = 800
    margin_left: int = 80
    margin_right: int = 80
    margin_top: int = 60
    margin_bottom: int = 60
    font_size: int = 24
    line_spacing: float = 1.5
    paragraph_spacing: float = 1.0
    font_path: Optional[str] = None
    script: str = "Devanagari"
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    effects: EffectsConfig = field(default_factory=EffectsConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)

    def __post_init__(self) -> None:
        if self.page_width <= 0 or self.page_height <= 0:
            raise ValueError(
                f"Page dimensions must be positive, got {self.page_width}x{self.page_height}"
            )
        if (
            self.margin_left < 0
            or self.margin_right < 0
            or self.margin_top < 0
            or self.margin_bottom < 0
        ):
            raise ValueError("Margins cannot be negative")
        if self.usable_width <= 0:
            raise ValueError(
                f"Usable width ({self.usable_width}) must be positive. "
                f"Page width {self.page_width} <= margins {self.margin_left} + {self.margin_right}"
            )
        if self.usable_height <= 0:
            raise ValueError(
                f"Usable height ({self.usable_height}) must be positive. "
                f"Page height {self.page_height} <= margins {self.margin_top} + {self.margin_bottom}"
            )
        if self.font_size <= 0:
            raise ValueError(f"font_size must be positive, got {self.font_size}")
        if self.line_spacing <= 0:
            raise ValueError(f"line_spacing must be positive, got {self.line_spacing}")
        if self.paragraph_spacing < 0:
            raise ValueError(
                f"paragraph_spacing must be non-negative, got {self.paragraph_spacing}"
            )

        estimated_line_height = int(math.ceil(self.font_size * self.line_spacing))
        if estimated_line_height > self.usable_height:
            raise ValueError(
                f"Estimated line height ({estimated_line_height}px) exceeds usable height ({self.usable_height}px)"
            )

    @property
    def usable_width(self) -> int:
        """Usable horizontal width available for text."""
        return self.page_width - self.margin_left - self.margin_right

    @property
    def usable_height(self) -> int:
        """Usable vertical height available for text."""
        return self.page_height - self.margin_top - self.margin_bottom
