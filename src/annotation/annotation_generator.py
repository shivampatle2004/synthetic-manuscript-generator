"""Ground-truth Markdown annotation generator synchronized with LayoutPage."""

from pathlib import Path
from typing import Optional, Union

from src.layout.layout_engine import LayoutPage


class AnnotationGenerator:
    """Generates structured, synchronized Markdown ground-truth annotations from LayoutPage."""

    def __init__(
        self,
        script: str = "Devanagari",
        layout_style: str = "traditional_single",
    ) -> None:
        self.script = script
        self.layout_style = layout_style

    def generate_markdown(
        self,
        layout_page: LayoutPage,
        image_filename: Optional[str] = None,
        script: Optional[str] = None,
        layout_style: Optional[str] = None,
    ) -> str:
        """Produce deterministic, structured Markdown from a single LayoutPage.

        Preserves exact textual content, block positions, font sizes, section markers,
        and highlight annotations without rewriting, summarizing, or altering characters.
        """
        img_name = (
            image_filename
            if image_filename is not None
            else f"Image_{layout_page.page_number:03d}.png"
        )
        active_script = script or self.script
        active_layout = layout_style or self.layout_style

        lines: list[str] = []

        # 1. Document Title
        lines.append("# Manuscript Page")
        lines.append("")

        # 2. Metadata Section
        lines.append("## Metadata")
        lines.append("")
        lines.append(f"- Image: {img_name}")
        lines.append(f"- Page: {layout_page.page_number}")
        lines.append(f"- Script: {active_script}")
        lines.append(f"- Layout: {active_layout}")
        lines.append(f"- Dimensions: {layout_page.width}x{layout_page.height}")
        lines.append("")

        # 3. Main Text Section (concatenated primary manuscript body)
        main_blocks = [b for b in layout_page.blocks if b.role == "main_text"]
        main_text_content = "\n\n".join(b.text.strip() for b in main_blocks if b.text.strip())

        lines.append("## Main Text")
        lines.append("")
        if main_text_content:
            lines.append(main_text_content)
        else:
            lines.append("None")
        lines.append("")

        # 4. Detailed Structured Blocks Section
        lines.append("## Blocks")
        lines.append("")
        for block in layout_page.blocks:
            lines.append(f"### Block: {block.role}")
            lines.append("")
            lines.append(f"- Block ID: {block.block_id}")
            lines.append(f"- Role: {block.role}")
            lines.append(f"- Position: x={block.x}, y={block.y}")
            lines.append(f"- Size: width={block.width}, height={block.height}")
            if block.font_size is not None:
                lines.append(f"- Font Size: {block.font_size}")
            if block.line_height is not None:
                lines.append(f"- Line Height: {block.line_height}")
            lines.append(f"- Highlighted: {str(block.highlighted).lower()}")
            lines.append("")
            lines.append("Text:")
            lines.append("")
            lines.append(block.text.strip())
            lines.append("")

        # 5. Section Markers Section
        lines.append("## Section Markers")
        lines.append("")
        if layout_page.markers:
            for marker in layout_page.markers:
                lines.append(f"- Marker ID: {marker.marker_id}")
                lines.append(f"  Type: {marker.marker_type}")
                lines.append(f"  Position: x={marker.x}, y={marker.y}")
                lines.append(f"  Size: width={marker.width}, height={marker.height}")
        else:
            lines.append("None")
        lines.append("")

        # 6. Highlights Section
        lines.append("## Highlights")
        lines.append("")
        highlighted_blocks = [b for b in layout_page.blocks if b.highlighted]
        if highlighted_blocks:
            for h_block in highlighted_blocks:
                color_str = str(h_block.highlight_color) if h_block.highlight_color else "default"
                lines.append(f"- Block: {h_block.block_id}")
                lines.append(f"  Role: {h_block.role}")
                lines.append(f"  Color: {color_str}")
        else:
            lines.append("None")
        lines.append("")

        return "\n".join(lines)

    def generate_annotation(
        self,
        layout_page: LayoutPage,
        output_path: Union[str, Path],
        image_filename: Optional[str] = None,
        script: Optional[str] = None,
        layout_style: Optional[str] = None,
    ) -> Path:
        """Write ground-truth Markdown file for the given LayoutPage in UTF-8."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        content = self.generate_markdown(
            layout_page=layout_page,
            image_filename=image_filename,
            script=script,
            layout_style=layout_style,
        )

        target.write_text(content, encoding="utf-8")
        return target
