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
    # Single Manuscript Generation Options
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
        help="Output directory for rendered PNG page images and ground-truth MD annotations",
    )
    parser.add_argument(
        "--font",
        "-f",
        type=str,
        default=None,
        help="Path to TTF/OTF/TTC font file",
    )
    parser.add_argument(
        "--background",
        "-b",
        type=str,
        default="paper",
        choices=["paper", "palm_leaf"],
        help="Historical background material type ('paper' or 'palm_leaf')",
    )
    parser.add_argument(
        "--layout",
        "-l",
        type=str,
        default="traditional_single",
        choices=["traditional_single", "side_annotation", "multi_block"],
        help="Manuscript page layout style ('traditional_single', 'side_annotation', 'multi_block')",
    )
    parser.add_argument(
        "--script",
        type=str,
        default="Devanagari",
        help="Target manuscript script (e.g. Devanagari, Modi, Sharada)",
    )
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=None,
        help="Random seed for reproducible procedural generation",
    )
    parser.add_argument(
        "--layout-seed",
        type=int,
        default=None,
        help="Random seed specifically for layout variation",
    )
    parser.add_argument(
        "--highlight",
        action="store_true",
        default=False,
        help="Enable authentic historical pigment wash highlight on key text",
    )
    parser.add_argument(
        "--no-effects",
        action="store_true",
        default=False,
        help="Disable physical manuscript effects (warp, folds, ink bleed, fade)",
    )
    parser.add_argument(
        "--effects-strength",
        type=float,
        default=0.3,
        help="Intensity scaling for physical manuscript effects (default: 0.3)",
    )
    parser.add_argument(
        "--effects-seed",
        type=int,
        default=None,
        help="Random seed specifically for physical effects layer",
    )
    parser.add_argument(
        "--scribal-variation",
        action="store_true",
        default=False,
        help="Enable subtle organic scribal line jitter and baseline undulation",
    )
    parser.add_argument(
        "--scribal-strength",
        type=float,
        default=0.6,
        help="Intensity scaling for scribal line variation (default: 0.6)",
    )

    # Multi-Script Dataset Generation Options
    parser.add_argument(
        "--dataset",
        action="store_true",
        default=False,
        help="Run in multi-script dataset generation mode",
    )
    parser.add_argument(
        "--dataset-output",
        type=str,
        default="dataset",
        help="Output root directory for generated dataset (default: 'dataset')",
    )
    parser.add_argument(
        "--dataset-seed",
        type=int,
        default=42,
        help="Master seed for reproducible dataset generation (default: 42)",
    )
    parser.add_argument(
        "--samples-per-script",
        type=int,
        default=100,
        help="Number of samples to generate per script (default: 100)",
    )
    parser.add_argument(
        "--scripts",
        type=str,
        default="Devanagari,Modi,Sharada",
        help="Comma-separated list of scripts to generate (default: 'Devanagari,Modi,Sharada')",
    )
    parser.add_argument(
        "--train-count",
        type=int,
        default=None,
        help="Explicit sample count for train split",
    )
    parser.add_argument(
        "--validation-count",
        type=int,
        default=None,
        help="Explicit sample count for validation split",
    )
    parser.add_argument(
        "--test-count",
        type=int,
        default=None,
        help="Explicit sample count for test split",
    )
    parser.add_argument(
        "--devanagari-font",
        type=str,
        default=None,
        help="Custom font path for Devanagari script",
    )
    parser.add_argument(
        "--modi-font",
        type=str,
        default=None,
        help="Custom font path for Modi script",
    )
    parser.add_argument(
        "--sharada-font",
        type=str,
        default=None,
        help="Custom font path for Sharada script",
    )
    parser.add_argument(
        "--devanagari-input",
        type=str,
        default=None,
        help="Custom manuscript input path for Devanagari script",
    )
    parser.add_argument(
        "--modi-input",
        type=str,
        default=None,
        help="Custom manuscript input path for Modi script",
    )
    parser.add_argument(
        "--sharada-input",
        type=str,
        default=None,
        help="Custom manuscript input path for Sharada script",
    )
    return parser


def main() -> int:
    """Main CLI entry point for pipeline orchestration."""
    parser = build_parser()
    args = parser.parse_args()

    # 1. Dataset Generation Mode
    if args.dataset:
        from src.config.script_config import DatasetConfig, ScriptConfig
        from src.dataset.dataset_builder import DatasetBuilder

        total_s = args.samples_per_script
        if (
            args.train_count is not None
            and args.validation_count is not None
            and args.test_count is not None
        ):
            tr, va, te = args.train_count, args.validation_count, args.test_count
        elif total_s == 100:
            tr, va, te = 85, 10, 5
        elif total_s == 3:
            tr, va, te = 1, 1, 1
        else:
            tr = int(round(total_s * 0.85))
            va = int(round(total_s * 0.10))
            te = total_s - tr - va
            if te < 0:
                te = 0
                tr = total_s - va

        requested_scripts = [
            s.strip() for s in args.scripts.split(",") if s.strip()
        ]
        script_configs = []
        for sname in requested_scripts:
            font_p = None
            input_p = None
            s_low = sname.lower()
            if s_low == "devanagari":
                font_p = args.devanagari_font
                input_p = args.devanagari_input or "input/devanagari.md"
            elif s_low == "modi":
                font_p = args.modi_font
                input_p = args.modi_input or "input/modi.md"
            elif s_low == "sharada":
                font_p = args.sharada_font
                input_p = args.sharada_input or "input/sharada.md"

            script_configs.append(
                ScriptConfig(
                    name=sname,
                    font_path=font_p,
                    input_path=input_p,
                    enabled=True,
                )
            )

        dataset_config = DatasetConfig(
            samples_per_script=total_s,
            train_count=tr,
            validation_count=va,
            test_count=te,
            scripts=script_configs,
            output_dir=args.dataset_output,
            seed=args.dataset_seed,
        )

        builder = DatasetBuilder(config=dataset_config)
        summary = builder.build()
        print(summary.format_summary())
        return 0

    # 2. Single Manuscript Generation Mode
    if args.input:
        from src.annotation.annotation_generator import AnnotationGenerator
        from src.config.settings import (
            BackgroundConfig,
            EffectsConfig,
            LayoutConfig,
            PageConfig,
        )
        from src.input.manuscript_loader import ManuscriptLoader
        from src.layout.layout_engine import LayoutEngine
        from src.pagination.page_builder import PageBuilder
        from src.rendering.text_renderer import (
            ManuscriptRenderer,
            find_default_indic_font,
        )

        loader = ManuscriptLoader()
        manuscript = loader.load(args.input)

        chosen_font = args.font or find_default_indic_font()
        bg_config = BackgroundConfig(
            background_type=args.background,
            seed=args.seed,
        )

        eff_seed = args.effects_seed if args.effects_seed is not None else args.seed
        strength = max(0.0, min(2.0, args.effects_strength))
        effects_config = EffectsConfig(
            enabled=not args.no_effects,
            warp_strength=strength,
            fold_strength=strength,
            ink_bleed_strength=strength,
            fade_strength=strength,
            smudge_strength=min(0.5, strength * 0.7),
            edge_wear_strength=strength,
            enable_scribal_variation=args.scribal_variation,
            scribal_variation_strength=max(0.0, min(2.0, args.scribal_strength)),
            seed=eff_seed,
        )

        lay_seed = args.layout_seed if args.layout_seed is not None else args.seed
        layout_config = LayoutConfig(
            layout_style=args.layout,
            highlights_enabled=args.highlight,
            seed=lay_seed,
        )

        config = PageConfig(
            font_path=chosen_font,
            script=args.script,
            background=bg_config,
            effects=effects_config,
            layout=layout_config,
        )
        paginator = PageBuilder(config=config)
        pages = paginator.paginate(manuscript)

        if args.output:
            out_dir = Path(args.output)
            out_dir.mkdir(parents=True, exist_ok=True)

            layout_engine = LayoutEngine(config=config.layout)
            renderer = ManuscriptRenderer(
                config=config, font_path=chosen_font, layout_engine=layout_engine
            )
            annotation_gen = AnnotationGenerator(
                script=args.script, layout_style=args.layout
            )

            rendered_items: list[Path] = []
            for page in pages:
                # 1. Build synchronized LayoutPage
                lpage = layout_engine.build_layout(page, config.layout, config)

                img_name = f"Image_{lpage.page_number:03d}.png"
                md_name = f"Image_{lpage.page_number:03d}.md"

                img_path = out_dir / img_name
                md_path = out_dir / md_name

                # 2. Render PNG from LayoutPage
                renderer.render_layout_page(lpage, img_path)
                rendered_items.append(img_path)

                # 3. Generate ground-truth MD from identical LayoutPage
                annotation_gen.generate_annotation(
                    lpage,
                    output_path=md_path,
                    image_filename=img_name,
                    script=args.script,
                    layout_style=args.layout,
                )
                rendered_items.append(md_path)

            print(f"Loaded manuscript: {args.input}")
            print(f"Pages generated: {len(pages)}")
            print("Rendered:")
            for item in rendered_items:
                clean_path = str(item).replace("\\", "/")
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
