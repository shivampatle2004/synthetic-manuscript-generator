"""Basic manuscript page image renderer for converting PageContent to PNG."""

import math
from pathlib import Path
from typing import List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont

from src.config.settings import PageConfig
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
    """Renders paginated manuscript pages to PNG images with paper background and ink typography."""

    def __init__(
        self,
        config: Optional[PageConfig] = None,
        font_path: Optional[Union[str, Path]] = None,
        bg_color: Tuple[int, int, int] = (248, 244, 232),  # Warm off-white parchment
        text_color: Tuple[int, int, int] = (42, 32, 24),    # Dark historic brown-black ink
    ) -> None:
        self.config = config or PageConfig()
        self.bg_color = bg_color
        self.text_color = text_color

        # Resolve font path priority: explicit parameter -> config -> auto-discovered
        candidate_font = font_path if font_path is not None else self.config.font_path
        self.font_path: Optional[str] = str(candidate_font) if candidate_font else None

        self.font = self._resolve_and_load_font()
        self.line_height = self._calculate_line_height()

    def _resolve_and_load_font(self) -> ImageFont.ImageFont:
        """Resolve and load the configured TrueType/OpenType font or fallback safely."""
        if self.font_path:
            p = Path(self.font_path)
            if not p.exists():
                raise FileNotFoundError(f"Configured font file not found: {p.resolve()}")
            try:
                return ImageFont.truetype(str(p), size=self.config.font_size)
            except Exception as exc:
                raise ValueError(f"Failed to load font from {p.resolve()}: {exc}") from exc

        # If font_path was not explicitly provided, try candidate Indic font
        discovered = find_default_indic_font()
        if discovered:
            try:
                return ImageFont.truetype(discovered, size=self.config.font_size)
            except Exception:
                pass

        # Fallback to Pillow's scalable default font
        try:
            return ImageFont.load_default(size=self.config.font_size)
        except TypeError:
            return ImageFont.load_default()

    def _calculate_line_height(self) -> int:
        """Calculate line height matching PageBuilder line measurement."""
        bbox = self.font.getbbox("Aygy|Éअक")
        char_height = (bbox[3] - bbox[1]) if bbox else self.config.font_size
        base_height = max(char_height, self.config.font_size)
        return max(1, int(math.ceil(base_height * self.config.line_spacing)))

    def create_page_background(self, width: int, height: int) -> Image.Image:
        """Create basic manuscript page canvas.

        Kept separate from text drawing so that future stages can replace or
        enhance this with realistic historical background textures.
        """
        return Image.new("RGB", (width, height), color=self.bg_color)

    def render_page(self, page: PageContent, output_path: Union[str, Path]) -> Path:
        """Render a single PageContent object into a PNG file.

        Verifies that:
        - Image dimensions match page_width x page_height.
        - Text is positioned inside the configured margins.
        - Output directory is created if needed.
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        img = self.create_page_background(self.config.page_width, self.config.page_height)
        draw = ImageDraw.Draw(img)

        margin_left = self.config.margin_left
        margin_top = self.config.margin_top
        max_y = self.config.page_height - self.config.margin_bottom
        paragraph_gap = int(self.config.paragraph_spacing * self.line_height)

        current_y = margin_top

        if page.paragraphs:
            for idx, para in enumerate(page.paragraphs):
                for line in para.splitlines():
                    if current_y + self.line_height <= max_y:
                        draw.text(
                            (margin_left, current_y),
                            line,
                            fill=self.text_color,
                            font=self.font,
                        )
                    current_y += self.line_height
                if idx < len(page.paragraphs) - 1:
                    current_y += paragraph_gap
        else:
            for line in page.lines:
                if current_y + self.line_height <= max_y:
                    draw.text(
                        (margin_left, current_y),
                        line,
                        fill=self.text_color,
                        font=self.font,
                    )
                current_y += self.line_height

        img.save(out_file, format="PNG")
        return out_file

    def render_pages(
        self,
        pages: List[PageContent],
        output_dir: Union[str, Path],
        prefix: str = "Image_",
    ) -> List[Path]:
        """Render a sequence of PageContent objects into sequential PNG files."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        rendered_paths: List[Path] = []
        for page in pages:
            file_name = f"{prefix}{page.page_number:03d}.png"
            target_path = out_dir / file_name
            self.render_page(page, target_path)
            rendered_paths.append(target_path)

        return rendered_paths
