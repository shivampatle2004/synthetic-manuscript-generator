"""Advanced historical manuscript layout engine supporting multi-block and annotated structures."""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from src.config.settings import LayoutConfig, PageConfig
from src.pagination.page_builder import PageContent


@dataclass
class TextBlock:
    """Represents a discrete text block positioned on a manuscript page."""

    block_id: str
    text: str
    lines: List[str]
    x: int
    y: int
    width: int
    height: int
    role: str = "main_text"  # "main_text", "side_text", "marginal_text", "section", "highlight"
    font_size: Optional[int] = None
    line_height: Optional[int] = None
    highlighted: bool = False
    highlight_color: Optional[Tuple[int, int, int]] = None

    @property
    def bounding_box(self) -> Tuple[int, int, int, int]:
        """(x0, y0, x1, y1) bounding coordinates."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)


@dataclass
class SectionMarker:
    """Decorative or structural section/punctuation marker on a manuscript folio."""

    marker_id: str
    marker_type: str  # "flourish", "danda_divider", "lotus", "heading_rule"
    x: int
    y: int
    width: int
    height: int
    color: Optional[Tuple[int, int, int]] = None

    @property
    def bounding_box(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


@dataclass
class LayoutPage:
    """Complete layout specification for a single manuscript page."""

    page_number: int
    width: int
    height: int
    blocks: List[TextBlock] = field(default_factory=list)
    markers: List[SectionMarker] = field(default_factory=list)

    @property
    def main_text_blocks(self) -> List[TextBlock]:
        """List of blocks carrying primary manuscript text."""
        return [b for b in self.blocks if b.role == "main_text"]

    @property
    def side_text_blocks(self) -> List[TextBlock]:
        """List of secondary commentary or marginal gloss blocks."""
        return [b for b in self.blocks if b.role in ("side_text", "marginal_text")]


def check_collision(
    box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int]
) -> bool:
    """Check if two bounding boxes (x0, y0, x1, y1) overlap."""
    ax0, ay0, ax1, ay1 = box_a
    bx0, by0, bx1, by1 = box_b
    return not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)


class LayoutEngine:
    """Lays out paginated manuscript text into structured, historically authentic folio designs."""

    def __init__(self, config: Optional[LayoutConfig] = None) -> None:
        self.config = config or LayoutConfig()

    def build_layout(
        self,
        page: PageContent,
        layout_config: Optional[LayoutConfig] = None,
        page_config: Optional[PageConfig] = None,
    ) -> LayoutPage:
        """Construct a LayoutPage from paginated PageContent.

        Guarantees:
        - All manuscript text lines are preserved without omission or duplication.
        - All elements strictly remain inside the configured page bounds.
        - Text blocks do not unintentionally collide.
        - Deterministic layout variation driven by seed.
        """
        cfg = layout_config or self.config
        p_cfg = page_config or PageConfig()

        active_seed = (
            cfg.seed + page.page_number
            if cfg.seed is not None
            else page.page_number
        )
        rng = np.random.default_rng(active_seed)

        style = cfg.layout_style

        if style == "side_annotation":
            return self._build_side_annotation_layout(page, cfg, p_cfg, rng)
        elif style == "multi_block":
            return self._build_multi_block_layout(page, cfg, p_cfg, rng)
        else:
            return self._build_traditional_single_layout(page, cfg, p_cfg, rng)

    def _build_traditional_single_layout(
        self,
        page: PageContent,
        cfg: LayoutConfig,
        p_cfg: PageConfig,
        rng: np.random.Generator,
    ) -> LayoutPage:
        """Traditional single centered manuscript text block with optional section marker and highlight."""
        usable_w = p_cfg.usable_width
        usable_h = p_cfg.usable_height

        # Subtle organic positional jitter within safe margins
        max_jitter = int(cfg.layout_variation * 8.0)
        jx = int(rng.integers(-max_jitter, max_jitter + 1)) if max_jitter > 0 else 0
        jy = int(rng.integers(-max_jitter, max_jitter + 1)) if max_jitter > 0 else 0

        bx = p_cfg.margin_left + jx
        by = p_cfg.margin_top + jy

        # Calculate block height based on lines
        line_h = int(math.ceil(p_cfg.font_size * p_cfg.line_spacing))
        block_h = min(usable_h, len(page.lines) * line_h + 10)

        # Highlight support (subtle historic pigment wash)
        is_highlighted = cfg.highlights_enabled
        highlight_color = (236, 188, 120) if is_highlighted else None  # Warm turmeric wash

        main_block = TextBlock(
            block_id=f"page_{page.page_number}_main",
            text=page.text,
            lines=list(page.lines),
            x=bx,
            y=by,
            width=usable_w,
            height=block_h,
            role="main_text",
            font_size=p_cfg.font_size,
            line_height=line_h,
            highlighted=is_highlighted,
            highlight_color=highlight_color,
        )

        markers: List[SectionMarker] = []
        if cfg.section_markers_enabled and page.page_number == 1:
            marker_w, marker_h = 60, 16
            mx = bx + (usable_w - marker_w) // 2
            my = max(10, by - 28)
            markers.append(
                SectionMarker(
                    marker_id=f"marker_top_{page.page_number}",
                    marker_type="lotus",
                    x=mx,
                    y=my,
                    width=marker_w,
                    height=marker_h,
                    color=(168, 44, 32),  # Traditional vermilion red
                )
            )

        layout_page = LayoutPage(
            page_number=page.page_number,
            width=p_cfg.page_width,
            height=p_cfg.page_height,
            blocks=[main_block],
            markers=markers,
        )
        self._validate_boundaries(layout_page, p_cfg)
        return layout_page

    def _build_side_annotation_layout(
        self,
        page: PageContent,
        cfg: LayoutConfig,
        p_cfg: PageConfig,
        rng: np.random.Generator,
    ) -> LayoutPage:
        """Historical Indic commentary (tika/vritti) layout with main text and side gloss column."""
        usable_w = p_cfg.usable_width
        usable_h = p_cfg.usable_height
        margin_l = p_cfg.margin_left
        margin_t = p_cfg.margin_top

        # Layout geometry: 72% main text, 6% gutter, 22% side annotation
        main_w = int(usable_w * 0.72)
        gutter = int(usable_w * 0.05)
        side_w = usable_w - main_w - gutter
        side_x = margin_l + main_w + gutter

        line_h = int(math.ceil(p_cfg.font_size * p_cfg.line_spacing))
        main_h = min(usable_h, len(page.lines) * line_h + 10)

        main_block = TextBlock(
            block_id=f"page_{page.page_number}_main",
            text=page.text,
            lines=list(page.lines),
            x=margin_l,
            y=margin_t,
            width=main_w,
            height=main_h,
            role="main_text",
            font_size=p_cfg.font_size,
            line_height=line_h,
        )

        # Side commentary / gloss lines
        side_lines = (
            cfg.side_text_content.splitlines()
            if cfg.side_text_content
            else ["॥ टीका ॥", "अत्र श्लोके", "पदच्छेदः", "अन्वयार्थः च ।"]
        )
        side_font_size = max(12, int(p_cfg.font_size * 0.65))
        side_line_h = int(math.ceil(side_font_size * 1.4))
        side_h = min(usable_h, len(side_lines) * side_line_h + 10)

        side_block = TextBlock(
            block_id=f"page_{page.page_number}_side",
            text="\n".join(side_lines),
            lines=side_lines,
            x=side_x,
            y=margin_t + 10,
            width=side_w,
            height=side_h,
            role="side_text",
            font_size=side_font_size,
            line_height=side_line_h,
        )

        markers: List[SectionMarker] = []
        if cfg.section_markers_enabled:
            # Subtle vertical separating rule between main text and side commentary
            markers.append(
                SectionMarker(
                    marker_id=f"gutter_rule_{page.page_number}",
                    marker_type="heading_rule",
                    x=margin_l + main_w + (gutter // 2),
                    y=margin_t,
                    width=2,
                    height=min(usable_h, max(main_h, side_h)),
                    color=(180, 160, 130),
                )
            )

        layout_page = LayoutPage(
            page_number=page.page_number,
            width=p_cfg.page_width,
            height=p_cfg.page_height,
            blocks=[main_block, side_block],
            markers=markers,
        )
        self._validate_boundaries(layout_page, p_cfg)
        return layout_page

    def _build_multi_block_layout(
        self,
        page: PageContent,
        cfg: LayoutConfig,
        p_cfg: PageConfig,
        rng: np.random.Generator,
    ) -> LayoutPage:
        """Dual manuscript section layout with primary verse text and explanatory lower text."""
        usable_w = p_cfg.usable_width
        usable_h = p_cfg.usable_height
        margin_l = p_cfg.margin_left
        margin_t = p_cfg.margin_top

        line_h = int(math.ceil(p_cfg.font_size * p_cfg.line_spacing))
        total_lines = len(page.lines)

        # Logically split lines between upper and lower block
        split_idx = max(1, total_lines // 2)
        top_lines = page.lines[:split_idx]
        bottom_lines = page.lines[split_idx:]

        top_h = max(20, len(top_lines) * line_h)
        block_top = TextBlock(
            block_id=f"page_{page.page_number}_block_1",
            text="\n".join(top_lines),
            lines=list(top_lines),
            x=margin_l,
            y=margin_t,
            width=usable_w,
            height=top_h,
            role="main_text",
            font_size=p_cfg.font_size,
            line_height=line_h,
        )

        # Central decorative danda divider
        divider_y = margin_t + top_h + 12
        divider = SectionMarker(
            marker_id=f"divider_{page.page_number}",
            marker_type="danda_divider",
            x=margin_l + int(usable_w * 0.15),
            y=divider_y,
            width=int(usable_w * 0.70),
            height=14,
            color=(160, 40, 30),
        )

        bottom_y = divider_y + 22
        bottom_h = max(20, len(bottom_lines) * line_h)
        block_bottom = TextBlock(
            block_id=f"page_{page.page_number}_block_2",
            text="\n".join(bottom_lines),
            lines=list(bottom_lines),
            x=margin_l,
            y=bottom_y,
            width=usable_w,
            height=bottom_h,
            role="main_text",
            font_size=p_cfg.font_size,
            line_height=line_h,
        )

        layout_page = LayoutPage(
            page_number=page.page_number,
            width=p_cfg.page_width,
            height=p_cfg.page_height,
            blocks=[block_top, block_bottom],
            markers=[divider],
        )
        self._validate_boundaries(layout_page, p_cfg)
        return layout_page

    def _validate_boundaries(
        self, layout_page: LayoutPage, p_cfg: PageConfig
    ) -> None:
        """Validate that all text blocks stay inside the page dimensions and do not collide."""
        for block in layout_page.blocks:
            if block.x < 0 or block.y < 0:
                raise ValueError(
                    f"Block {block.block_id} positioned outside left/top: ({block.x}, {block.y})"
                )
            if block.x + block.width > p_cfg.page_width:
                raise ValueError(
                    f"Block {block.block_id} exceeds page width: {block.x + block.width} > {p_cfg.page_width}"
                )
            if block.y + block.height > p_cfg.page_height:
                raise ValueError(
                    f"Block {block.block_id} exceeds page height: {block.y + block.height} > {p_cfg.page_height}"
                )

        # Check collisions between blocks
        num_blocks = len(layout_page.blocks)
        for i in range(num_blocks):
            for j in range(i + 1, num_blocks):
                b1 = layout_page.blocks[i]
                b2 = layout_page.blocks[j]
                if check_collision(b1.bounding_box, b2.bounding_box):
                    raise ValueError(
                        f"Collision detected between {b1.block_id} and {b2.block_id}"
                    )
