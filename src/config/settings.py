"""Configuration settings for page geometry, typography, and pagination."""

import math
from dataclasses import dataclass
from typing import Optional


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
