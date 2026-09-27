"""Manuscript page image renderer for converting PageContent and LayoutPage to PNG."""

import math
from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np
import scipy.ndimage
from PIL import Image, ImageDraw, ImageFont

from src.background.background_generator import BackgroundGenerator
from src.config.settings import PageConfig
from src.effects.manuscript_effects import ManuscriptEffects
from src.layout.layout_engine import LayoutEngine, LayoutPage, SectionMarker, TextBlock
from src.pagination.page_builder import PageContent


def find_default_indic_font() -> Optional[str]:
    """Find a candidate Indic-capable font from assets or system paths."""
    # 1. Check local assets/fonts directory
    assets_dir = Path("assets/fonts")
    if assets_dir.exists():
        for pattern in ("*.ttf", "*.otf", "*.ttc"):
            for font_file in assets_dir.glob(pattern):
                return str(font_file.resolve())

    # 2. Check Windows standard Indic font (Nirmala UI / Nirmala)
    windows_nirmala = Path("C:/Windows/Fonts/Nirmala.ttc")
    if windows_nirmala.exists():
        return str(windows_nirmala)

    # 3. Check common Linux Indic font paths
    linux_paths = [
        Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.otf"),
        Path("/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf"),
    ]
    for lp in linux_paths:
        if lp.exists():
            return str(lp)

    return None


class ManuscriptRenderer:
    """Renders paginated manuscript pages and layouts to PNG images with authentic typography and physical effects."""

    def __init__(
        self,
        config: Optional[PageConfig] = None,
        font_path: Optional[Union[str, Path]] = None,
        background_generator: Optional[BackgroundGenerator] = None,
        effects: Optional[ManuscriptEffects] = None,
        layout_engine: Optional[LayoutEngine] = None,
        bg_color: Optional[Tuple[int, int, int]] = None,
        text_color: Tuple[int, int, int] = (42, 32, 24),  # Dark historic brown-black ink
    ) -> None:
        self.config = config or PageConfig()
        self.text_color = text_color

        if bg_color is not None:
            self.config.background.base_color = bg_color

        self.background_generator = background_generator or BackgroundGenerator(
            config=self.config.background,
            width=self.config.page_width,
            height=self.config.page_height,
        )

        self.effects = effects or ManuscriptEffects(config=self.config.effects)
        self.layout_engine = layout_engine or LayoutEngine(config=self.config.layout)

        # Resolve font path priority: explicit parameter -> config -> auto-discovered
        candidate_font = font_path if font_path is not None else self.config.font_path
        self.font_path: Optional[str] = str(candidate_font) if candidate_font else None

        self.font = self._resolve_and_load_font(self.config.font_size)
        self.line_height = self._calculate_line_height(self.font, self.config.font_size)

    def _resolve_and_load_font(self, size: int) -> ImageFont.ImageFont:
        """Resolve and load the configured font at the specified point size."""
        if self.font_path:
            p = Path(self.font_path)
            if not p.exists():
                raise FileNotFoundError(f"Configured font file not found: {p.resolve()}")
            try:
                return ImageFont.truetype(str(p), size=size)
            except Exception as exc:
                raise ValueError(f"Failed to load font from {p.resolve()}: {exc}") from exc

        discovered = find_default_indic_font()
        if discovered:
            try:
                return ImageFont.truetype(discovered, size=size)
            except Exception:
                pass

        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

    def _calculate_line_height(self, font: ImageFont.ImageFont, font_size: int) -> int:
        """Calculate line height matching typography metrics."""
        bbox = font.getbbox("Aygy|Éअक")
        char_height = (bbox[3] - bbox[1]) if bbox else font_size
        base_height = max(char_height, font_size)
        return max(1, int(math.ceil(base_height * self.config.line_spacing)))

    def create_page_background(
        self, width: int, height: int, page_number: int = 1
    ) -> Image.Image:
        """Create manuscript page canvas via BackgroundGenerator."""
        base_seed = self.config.background.seed
        page_seed = (base_seed + page_number) if base_seed is not None else None
        return self.background_generator.generate(
            width=width, height=height, seed=page_seed
        )

    def _render_section_marker(
        self, draw: ImageDraw.ImageDraw, marker: SectionMarker
    ) -> None:
        """Draw traditional procedural Indic ornamental markers and flourishes."""
        color = marker.color or (168, 44, 32)  # Vermilion red
        cx = marker.x + marker.width // 2
        cy = marker.y + marker.height // 2

        if marker.marker_type in ("lotus", "flourish"):
            # Central auspicious diamond flourish with flanking dots and flourishes
            draw.polygon(
                [(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)],
                fill=color,
            )
            draw.ellipse([cx - 16, cy - 3, cx - 10, cy + 3], fill=color)
            draw.ellipse([cx + 10, cy - 3, cx + 16, cy + 3], fill=color)
            draw.line([(cx - 26, cy), (cx - 18, cy)], fill=color, width=2)
            draw.line([(cx + 18, cy), (cx + 26, cy)], fill=color, width=2)
        elif marker.marker_type == "danda_divider":
            # Horizontal ornamental dividing line with central diamond
            y_line = cy
            x_start = marker.x
            x_end = marker.x + marker.width
            mid_gap = 14
            draw.line([(x_start, y_line), (cx - mid_gap, y_line)], fill=color, width=1)
            draw.line([(cx + mid_gap, y_line), (x_end, y_line)], fill=color, width=1)
            draw.polygon(
                [(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)],
                fill=color,
            )
        elif marker.marker_type == "heading_rule":
            # Subtle vertical or horizontal separating rule
            draw.rectangle(
                [marker.x, marker.y, marker.x + marker.width, marker.y + marker.height],
                fill=color,
            )

    def _render_line(
        self,
        img: Image.Image,
        line: str,
        x: int,
        y: int,
        font: ImageFont.ImageFont,
        rng: Optional[np.random.Generator] = None,
        strength: float = 0.0,
    ) -> None:
        """Render a single line of text with optional subtle organic scribal variation."""
        if not line or not line.strip():
            return

        # If scribal variation is disabled or zero strength, render directly and fast
        if rng is None or strength <= 0.0:
            draw = ImageDraw.Draw(img)
            draw.text((x, y), line, fill=self.text_color, font=font)
            return

        bbox = font.getbbox(line)
        if not bbox or bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
            draw = ImageDraw.Draw(img)
            draw.text((x, y), line, fill=self.text_color, font=font)
            return

        # 1. Subtle line-start horizontal jitter: approximately +/- 1-3 px
        dx = float(rng.uniform(-2.0, 2.0) * strength)
        # 2. Very subtle baseline variation: approximately +/- 1-2 px
        dy = float(rng.uniform(-1.2, 1.2) * strength)

        # 3. Slight smooth/organic baseline drift across line
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        pad = 12

        strip_w = w + 2 * pad
        strip_h = h + 2 * pad

        strip = Image.new("RGBA", (strip_w, strip_h), (0, 0, 0, 0))
        d_strip = ImageDraw.Draw(strip)
        d_strip.text(
            (pad - bbox[0], pad - bbox[1]),
            line,
            fill=(*self.text_color, 255),
            font=font,
        )

        alpha = np.array(strip)[:, :, 3].astype(np.float32)
        H_s, W_s = alpha.shape

        # Organic undulation wave parameters across folio line
        tilt = float(rng.uniform(-0.8, 0.8) * strength)
        amplitude = float(rng.uniform(-0.8, 0.8) * strength)
        freq = float(rng.uniform(0.8, 1.6))
        phase = float(rng.uniform(0, 2 * math.pi))

        x_rel = (np.arange(W_s, dtype=np.float32) - pad) / max(1.0, float(w))
        drift = tilt * (x_rel - 0.5) + amplitude * np.sin(
            2.0 * math.pi * freq * x_rel + phase
        )

        y_coords, x_coords = np.mgrid[0:H_s, 0:W_s]
        y_shifted = y_coords - drift[None, :]

        shifted_alpha = scipy.ndimage.map_coordinates(
            alpha, [y_shifted, x_coords], order=1, mode="constant", cval=0.0
        )

        out_strip_arr = np.zeros((H_s, W_s, 4), dtype=np.uint8)
        out_strip_arr[:, :, :3] = self.text_color
        out_strip_arr[:, :, 3] = np.clip(shifted_alpha, 0, 255).astype(np.uint8)
        out_strip = Image.fromarray(out_strip_arr, mode="RGBA")

        paste_x = int(round(x + bbox[0] - pad + dx))
        paste_y = int(round(y + bbox[1] - pad + dy))
        img.paste(out_strip, (paste_x, paste_y), out_strip)

    def render_layout_page(
        self, layout_page: LayoutPage, output_path: Union[str, Path]
    ) -> Path:
        """Render a structured LayoutPage into a PNG file."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        img = self.create_page_background(
            layout_page.width, layout_page.height, page_number=layout_page.page_number
        )
        draw = ImageDraw.Draw(img)

        # 1. Render highlights first (semi-transparent authentic pigment washes behind text)
        for block in layout_page.blocks:
            if block.highlighted and block.highlight_color:
                h_col = block.highlight_color
                draw.rectangle(
                    [
                        block.x - 6,
                        block.y - 4,
                        block.x + block.width + 6,
                        block.y + block.height + 4,
                    ],
                    fill=h_col,
                )

        # 2. Render section and decorative markers
        for marker in layout_page.markers:
            self._render_section_marker(draw, marker)

        # Determine scribal variation settings and deterministic RNG
        scribal_enabled = (
            self.config.effects.enable_scribal_variation
            and self.config.effects.scribal_variation_strength > 0
        )
        base_seed = self.config.effects.seed
        page_seed = (
            (base_seed + layout_page.page_number)
            if base_seed is not None
            else (layout_page.page_number * 10007)
        )
        scribal_rng = (
            np.random.default_rng(page_seed)
            if scribal_enabled
            else None
        )
        scribal_strength = (
            self.config.effects.scribal_variation_strength
            if scribal_enabled
            else 0.0
        )

        # 3. Render text blocks
        for block in layout_page.blocks:
            b_size = block.font_size or self.config.font_size
            b_font = (
                self.font
                if b_size == self.config.font_size
                else self._resolve_and_load_font(b_size)
            )
            b_line_h = block.line_height or self._calculate_line_height(b_font, b_size)

            current_y = block.y
            for line in block.lines:
                self._render_line(
                    img=img,
                    line=line,
                    x=block.x,
                    y=current_y,
                    font=b_font,
                    rng=scribal_rng,
                    strength=scribal_strength,
                )
                current_y += b_line_h

        # 4. Physical manuscript effects
        if self.effects and self.config.effects.enabled:
            base_seed = self.config.effects.seed
            effect_seed = (
                (base_seed + layout_page.page_number)
                if base_seed is not None
                else None
            )
            img = self.effects.apply(img, seed=effect_seed)

        img.save(out_file, format="PNG")
        return out_file

    def render_page(
        self, page: Union[PageContent, LayoutPage], output_path: Union[str, Path]
    ) -> Path:
        """Render either a PageContent (via LayoutEngine) or a pre-built LayoutPage."""
        if isinstance(page, LayoutPage):
            return self.render_layout_page(page, output_path)

        # Convert PageContent into structured LayoutPage
        layout_page = self.layout_engine.build_layout(
            page, self.config.layout, self.config
        )
        return self.render_layout_page(layout_page, output_path)

    def render_pages(
        self,
        pages: Union[List[PageContent], List[LayoutPage]],
        output_dir: Union[str, Path],
        prefix: str = "Image_",
    ) -> List[Path]:
        """Render a sequence of pages into sequential PNG files."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        rendered_paths: List[Path] = []
        for page in pages:
            file_name = f"{prefix}{page.page_number:03d}.png"
            target_path = out_dir / file_name
            self.render_page(page, target_path)
            rendered_paths.append(target_path)

        return rendered_paths
