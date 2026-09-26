"""Synthetic Manuscript Generator.

Orchestrator and CLI entry point for the synthetic manuscript generation pipeline.
"""

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """Build command-line interface argument parser."""
    parser = argparse.ArgumentParser(
        description="Synthetic Manuscript Generator CLI Orchestrator"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=None,
        help="Path to input markdown manuscript file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output directory for rendered PNG page images",
    )
    parser.add_argument(
        "--font",
        "-f",
        type=str,
        default=None,
        help="Path to TTF/OTF/TTC font file",
    )
    return parser


def main() -> int:
    """Main CLI entry point for pipeline orchestration."""
    parser = build_parser()
    args = parser.parse_args()

    if args.input:
        from src.config.settings import PageConfig
        from src.input.manuscript_loader import ManuscriptLoader
        from src.pagination.page_builder import PageBuilder
        from src.rendering.text_renderer import (
            ManuscriptRenderer,
            find_default_indic_font,
        )

        loader = ManuscriptLoader()
        manuscript = loader.load(args.input)

        chosen_font = args.font or find_default_indic_font()
        config = PageConfig(font_path=chosen_font)
        paginator = PageBuilder(config=config)
        pages = paginator.paginate(manuscript)

        if args.output:
            renderer = ManuscriptRenderer(config=config, font_path=chosen_font)
            rendered_paths = renderer.render_pages(pages, output_dir=args.output)

            print(f"Loaded manuscript: {args.input}")
            print(f"Pages generated: {len(pages)}")
            print("Rendered:")
            for p in rendered_paths:
                # Format with forward slashes for clean portable terminal output
                clean_path = str(p).replace("\\", "/")
                print(f"  {clean_path}")
            return 0

        print(f"Loaded manuscript: {args.input}")
        print(f"Characters: {manuscript.character_count}")
        print(f"Pages generated: {len(pages)}")
        for page in pages:
            print(f"Page {page.page_number}: {page.line_count} lines")
        return 0

    print("Synthetic Manuscript Generator initialized. (Stage 1: Structure Ready)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
