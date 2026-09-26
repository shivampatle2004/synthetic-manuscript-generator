"""Synthetic Manuscript Generator.

Orchestrator and CLI entry point for the synthetic manuscript generation pipeline.
"""

import sys
import argparse


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
    return parser


def main() -> int:
    """Main CLI entry point for pipeline orchestration."""
    parser = build_parser()
    args = parser.parse_args()

    if args.input:
        from src.config.settings import PageConfig
        from src.input.manuscript_loader import ManuscriptLoader
        from src.pagination.page_builder import PageBuilder

        loader = ManuscriptLoader()
        manuscript = loader.load(args.input)

        config = PageConfig()
        paginator = PageBuilder(config=config)
        pages = paginator.paginate(manuscript)

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
