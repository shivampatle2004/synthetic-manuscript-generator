"""Dataset builder for multi-script synthetic manuscript generation."""

import hashlib
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from src.annotation.annotation_generator import AnnotationGenerator
from src.config.script_config import (
    DatasetConfig,
    ScriptConfig,
    resolve_script_font,
    resolve_script_input,
)
from src.config.settings import (
    BackgroundConfig,
    EffectsConfig,
    LayoutConfig,
    PageConfig,
)
from src.input.manuscript_loader import ManuscriptLoader
from src.layout.layout_engine import LayoutEngine
from src.pagination.page_builder import PageBuilder
from src.rendering.text_renderer import ManuscriptRenderer


@dataclass
class DatasetSummary:
    """Summary statistics and status of generated dataset."""

    total_images: int = 0
    total_annotations: int = 0
    script_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    missing_scripts: Dict[str, str] = field(default_factory=dict)
    manifest_path: Optional[str] = None

    def format_summary(self) -> str:
        """Format a human-readable summary matching project requirements."""
        lines = ["Dataset generation complete", ""]
        all_scripts = list(self.script_counts.keys()) + [
            s for s in self.missing_scripts.keys() if s not in self.script_counts
        ]
        for script in all_scripts:
            lines.append(f"{script}:")
            if script in self.script_counts:
                counts = self.script_counts[script]
                for split_name in ("train", "validation", "test"):
                    lines.append(f"    {split_name}: {counts.get(split_name, 0)}")
            elif script in self.missing_scripts:
                lines.append(f"    STATUS: NOT GENERATED ({self.missing_scripts[script]})")
            lines.append("")

        lines.append(f"Total images: {self.total_images}")
        lines.append(f"Total annotations: {self.total_annotations}")
        return "\n".join(lines)


class DatasetBuilder:
    """Orchestrates multi-script dataset generation with reproducible splits."""

    def __init__(self, config: Optional[DatasetConfig] = None) -> None:
        """Initialize DatasetBuilder with dataset configuration.

        Args:
            config: DatasetConfig instance. Defaults to standard 300-sample config.
        """
        self.config = config or DatasetConfig()
        self.loader = ManuscriptLoader()

    def build(self) -> DatasetSummary:
        """Execute the dataset generation pipeline for all configured scripts.

        Returns:
            DatasetSummary containing generated sample counts, missing scripts,
            and manifest location.
        """
        output_base = Path(self.config.output_dir)
        output_base.mkdir(parents=True, exist_ok=True)

        summary = DatasetSummary()
        manifest_records: List[dict] = []

        splits = [
            ("train", self.config.train_count),
            ("validation", self.config.validation_count),
            ("test", self.config.test_count),
        ]

        for script in self.config.scripts:
            if not script.enabled:
                continue

            # 1. Resolve script font and input strictly
            try:
                resolved_font = resolve_script_font(script.name, script.font_path)
            except FileNotFoundError as e:
                summary.missing_scripts[script.name] = str(e)
                print(f"[{script.name}] FONT NOT AVAILABLE: {e}")
                continue

            try:
                resolved_input = resolve_script_input(script.name, script.input_path)
            except FileNotFoundError as e:
                summary.missing_scripts[script.name] = str(e)
                print(f"[{script.name}] INPUT NOT AVAILABLE: {e}")
                continue

            # 2. Load manuscript and paginate
            manuscript = self.loader.load(resolved_input)
            base_page_config = PageConfig(
                font_path=resolved_font,
                script=script.name,
            )
            paginator = PageBuilder(config=base_page_config)
            base_pages = paginator.paginate(manuscript)

            if not base_pages:
                summary.missing_scripts[script.name] = (
                    f"Manuscript '{resolved_input}' yielded 0 pages."
                )
                continue

            script_dir_name = script.name.lower()
            summary.script_counts[script.name] = {
                "train": 0,
                "validation": 0,
                "test": 0,
            }

            global_sample_counter = 0

            # 3. Generate samples for each split
            for split_name, split_count in splits:
                if split_count <= 0:
                    continue

                split_dir = output_base / script_dir_name / split_name
                split_dir.mkdir(parents=True, exist_ok=True)

                for sample_idx in range(1, split_count + 1):
                    # Deterministic per-sample seed
                    seed_str = (
                        f"{self.config.seed}_{script.name}_{split_name}_{sample_idx}"
                    )
                    sample_seed_int = int(
                        hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8],
                        16,
                    )
                    sample_rng = random.Random(sample_seed_int)

                    # Controlled variation parameters
                    layout_style = sample_rng.choice(self.config.layouts)
                    bg_type = sample_rng.choices(["paper", "palm_leaf"], weights=[0.8, 0.2])[0]
                    bg_seed = sample_rng.randint(1, 1000000)
                    eff_seed = sample_rng.randint(1, 1000000)
                    lay_seed = sample_rng.randint(1, 1000000)

                    bg_config = BackgroundConfig(
                        background_type=bg_type,
                        texture_strength=round(sample_rng.uniform(0.35, 0.65), 2),
                        aging_strength=round(sample_rng.uniform(0.25, 0.55), 2),
                        stain_strength=round(sample_rng.uniform(0.15, 0.45), 2),
                        edge_variation=round(sample_rng.uniform(0.2, 0.5), 2),
                        seed=bg_seed,
                    )

                    effects_config = EffectsConfig(
                        enabled=True,
                        warp_strength=round(sample_rng.uniform(0.15, 0.4), 2),
                        fold_strength=round(sample_rng.uniform(0.15, 0.4), 2),
                        fold_count=sample_rng.choice([0, 1, 1, 2]),
                        ink_bleed_strength=round(sample_rng.uniform(0.15, 0.35), 2),
                        fade_strength=round(sample_rng.uniform(0.15, 0.4), 2),
                        smudge_strength=round(sample_rng.uniform(0.1, 0.25), 2),
                        edge_wear_strength=round(sample_rng.uniform(0.2, 0.4), 2),
                        seed=eff_seed,
                    )

                    layout_config = LayoutConfig(
                        layout_style=layout_style,
                        highlights_enabled=sample_rng.choice([True, False, False]),
                        layout_variation=round(sample_rng.uniform(0.1, 0.3), 2),
                        seed=lay_seed,
                    )

                    page_config = PageConfig(
                        font_path=resolved_font,
                        script=script.name,
                        background=bg_config,
                        effects=effects_config,
                        layout=layout_config,
                    )

                    # Select page content
                    source_page = base_pages[global_sample_counter % len(base_pages)]
                    global_sample_counter += 1

                    # Build layout and render
                    layout_engine = LayoutEngine(config=layout_config)
                    lpage = layout_engine.build_layout(
                        source_page, layout_config, page_config
                    )
                    lpage.page_number = sample_idx

                    renderer = ManuscriptRenderer(
                        config=page_config,
                        font_path=resolved_font,
                        layout_engine=layout_engine,
                    )
                    annotation_gen = AnnotationGenerator(
                        script=script.name,
                        layout_style=layout_style,
                    )

                    img_name = f"Image_{sample_idx:03d}.png"
                    md_name = f"Image_{sample_idx:03d}.md"

                    img_path = split_dir / img_name
                    md_path = split_dir / md_name

                    renderer.render_layout_page(lpage, img_path)
                    annotation_gen.generate_annotation(
                        lpage,
                        output_path=md_path,
                        image_filename=img_name,
                        script=script.name,
                        layout_style=layout_style,
                    )

                    summary.total_images += 1
                    summary.total_annotations += 1
                    summary.script_counts[script.name][split_name] += 1

                    manifest_records.append(
                        {
                            "sample_id": f"{script_dir_name}_{split_name}_{sample_idx:03d}",
                            "script": script.name,
                            "split": split_name,
                            "image_path": f"{script_dir_name}/{split_name}/{img_name}",
                            "annotation_path": f"{script_dir_name}/{split_name}/{md_name}",
                            "layout_style": layout_style,
                            "background_type": bg_type,
                            "seed": sample_seed_int,
                            "source_manuscript": resolved_input,
                        }
                    )

        # 4. Write manifest.json
        manifest_data = {
            "dataset_seed": self.config.seed,
            "samples_per_script": self.config.samples_per_script,
            "total_images": summary.total_images,
            "total_annotations": summary.total_annotations,
            "splits": {
                "train": self.config.train_count,
                "validation": self.config.validation_count,
                "test": self.config.test_count,
            },
            "samples": manifest_records,
        }
        manifest_path = output_base / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)

        summary.manifest_path = str(manifest_path).replace("\\", "/")
        return summary
