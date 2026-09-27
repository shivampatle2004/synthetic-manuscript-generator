"""Unit tests for dataset builder, multi-script configurations, and dataset generation."""

import json
from pathlib import Path
import pytest
from PIL import Image

from src.config.script_config import (
    DatasetConfig,
    ScriptConfig,
    get_default_scripts,
    resolve_script_font,
    resolve_script_input,
)
from src.dataset.dataset_builder import DatasetBuilder


@pytest.fixture
def devanagari_only_config(tmp_path: Path) -> DatasetConfig:
    """Fixture providing a lightweight 3-sample Devanagari dataset configuration."""
    return DatasetConfig(
        samples_per_script=3,
        train_count=1,
        validation_count=1,
        test_count=1,
        scripts=[
            ScriptConfig(
                name="Devanagari",
                input_path="input/devanagari.md",
                enabled=True,
            )
        ],
        output_dir=str(tmp_path / "dataset"),
        seed=42,
    )


def test_script_configuration() -> None:
    """Test ScriptConfig validation and attributes."""
    cfg = ScriptConfig(name="Devanagari", font_path="assets/fonts/custom.ttf")
    assert cfg.name == "Devanagari"
    assert cfg.font_path == "assets/fonts/custom.ttf"
    assert cfg.enabled is True

    with pytest.raises(ValueError, match="Script name cannot be empty"):
        ScriptConfig(name="")


def test_train_validation_test_counts() -> None:
    """Test standard 85/10/5 split count validation."""
    cfg = DatasetConfig(
        samples_per_script=100,
        train_count=85,
        validation_count=10,
        test_count=5,
    )
    assert cfg.train_count == 85
    assert cfg.validation_count == 10
    assert cfg.test_count == 5
    assert cfg.train_count + cfg.validation_count + cfg.test_count == 100


def test_invalid_split_configuration() -> None:
    """Test that mismatched split counts raise clear ValueError."""
    with pytest.raises(ValueError, match="must equal samples_per_script"):
        DatasetConfig(
            samples_per_script=100,
            train_count=80,
            validation_count=10,
            test_count=5,  # Sum = 95 != 100
        )

    with pytest.raises(ValueError, match="cannot be negative"):
        DatasetConfig(
            samples_per_script=10,
            train_count=-1,
            validation_count=6,
            test_count=5,
        )

    with pytest.raises(ValueError, match="must be positive"):
        DatasetConfig(
            samples_per_script=0,
            train_count=0,
            validation_count=0,
            test_count=0,
        )


def test_all_three_scripts_supported() -> None:
    """Verify Devanagari, Modi, and Sharada are configured and supported."""
    default_scripts = get_default_scripts()
    script_names = [s.name for s in default_scripts]
    assert "Devanagari" in script_names
    assert "Modi" in script_names
    assert "Sharada" in script_names


def test_script_font_resolution_and_missing_font_handling(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify that script fonts resolve strictly without fallback, and missing fonts raise clear errors."""
    # 1. Verify authentic fonts resolve to their own script files
    modi_font = resolve_script_font("Modi")
    assert "modi" in modi_font.lower()
    assert "devanagari" not in modi_font.lower()

    sharada_font = resolve_script_font("Sharada")
    assert "sharada" in sharada_font.lower()
    assert "devanagari" not in sharada_font.lower()

    devanagari_font = resolve_script_font("Devanagari")
    assert "devanagari" in devanagari_font.lower() or "nirmala" in devanagari_font.lower()

    # 2. Verify explicit non-existent font path raises clear FileNotFoundError
    with pytest.raises(FileNotFoundError) as exc_explicit:
        resolve_script_font("Modi", configured_font_path="nonexistent_font.ttf")
    assert "nonexistent_font.ttf" in str(exc_explicit.value)

    # 3. Verify missing font directory raises clear FileNotFoundError with setup message
    empty_fonts_dir = tmp_path / "empty_assets_fonts"
    empty_fonts_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("src.config.script_config.Path", lambda *p: empty_fonts_dir if "assets/fonts" in "/".join(p) else Path(*p))

    with pytest.raises(FileNotFoundError) as exc_modi:
        resolve_script_font("Modi")
    assert "Modi font not found" in str(exc_modi.value)
    assert "assets/fonts/modi" in str(exc_modi.value).replace("\\", "/")

    with pytest.raises(FileNotFoundError) as exc_sharada:
        resolve_script_font("Sharada")
    assert "Sharada font not found" in str(exc_sharada.value)
    assert "assets/fonts/sharada" in str(exc_sharada.value).replace("\\", "/")


def test_dataset_builder_directory_creation(devanagari_only_config: DatasetConfig) -> None:
    """Test that DatasetBuilder creates train, validation, and test directories."""
    builder = DatasetBuilder(config=devanagari_only_config)
    summary = builder.build()

    out_base = Path(devanagari_only_config.output_dir)
    assert (out_base / "devanagari" / "train").is_dir()
    assert (out_base / "devanagari" / "validation").is_dir()
    assert (out_base / "devanagari" / "test").is_dir()
    assert summary.total_images == 3
    assert summary.total_annotations == 3


def test_total_sample_count(devanagari_only_config: DatasetConfig) -> None:
    """Test total sample count matches sum of splits."""
    builder = DatasetBuilder(config=devanagari_only_config)
    summary = builder.build()

    dev_counts = summary.script_counts["Devanagari"]
    assert dev_counts["train"] == 1
    assert dev_counts["validation"] == 1
    assert dev_counts["test"] == 1
    assert summary.total_images == 3
    assert summary.total_annotations == 3


def test_png_md_pairing(devanagari_only_config: DatasetConfig) -> None:
    """Test that every generated PNG has an exact corresponding MD file."""
    builder = DatasetBuilder(config=devanagari_only_config)
    builder.build()

    out_base = Path(devanagari_only_config.output_dir) / "devanagari"
    for split in ("train", "validation", "test"):
        split_dir = out_base / split
        png_files = sorted(list(split_dir.glob("*.png")))
        md_files = sorted(list(split_dir.glob("*.md")))

        assert len(png_files) > 0
        assert len(png_files) == len(md_files)

        for png_file in png_files:
            md_file = png_file.with_suffix(".md")
            assert md_file.is_file(), f"Missing corresponding MD for {png_file}"

            # Verify image is valid PNG
            with Image.open(png_file) as img:
                assert img.format == "PNG"
                assert img.size == (1200, 800)

            # Verify MD file has structure
            content = md_file.read_text(encoding="utf-8")
            assert "# Manuscript Page" in content
            assert "## Metadata" in content
            assert "## Main Text" in content
            assert "## Blocks" in content


def test_no_duplicate_filenames_across_splits(
    devanagari_only_config: DatasetConfig,
) -> None:
    """Test sample paths and manifest IDs are globally unique."""
    builder = DatasetBuilder(config=devanagari_only_config)
    summary = builder.build()

    manifest_path = Path(summary.manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data["samples"]
    sample_ids = [s["sample_id"] for s in samples]
    image_paths = [s["image_path"] for s in samples]
    annotation_paths = [s["annotation_path"] for s in samples]

    assert len(sample_ids) == len(set(sample_ids)), "Duplicate sample_ids detected!"
    assert len(image_paths) == len(set(image_paths)), "Duplicate image_paths detected!"
    assert len(annotation_paths) == len(set(annotation_paths)), "Duplicate annotation_paths detected!"


def test_deterministic_seed_behavior(tmp_path: Path) -> None:
    """Test that identical seed produces identical manifest parameters."""
    cfg1 = DatasetConfig(
        samples_per_script=3,
        train_count=1,
        validation_count=1,
        test_count=1,
        scripts=[ScriptConfig(name="Devanagari", input_path="input/devanagari.md")],
        output_dir=str(tmp_path / "run1"),
        seed=123,
    )
    cfg2 = DatasetConfig(
        samples_per_script=3,
        train_count=1,
        validation_count=1,
        test_count=1,
        scripts=[ScriptConfig(name="Devanagari", input_path="input/devanagari.md")],
        output_dir=str(tmp_path / "run2"),
        seed=123,
    )

    DatasetBuilder(config=cfg1).build()
    DatasetBuilder(config=cfg2).build()

    with open(tmp_path / "run1" / "manifest.json", "r", encoding="utf-8") as f1:
        data1 = json.load(f1)
    with open(tmp_path / "run2" / "manifest.json", "r", encoding="utf-8") as f2:
        data2 = json.load(f2)

    assert data1["samples"] == data2["samples"]


def test_different_seed_produces_different_parameters(tmp_path: Path) -> None:
    """Test that different seed produces different sample seeds and parameters."""
    cfg1 = DatasetConfig(
        samples_per_script=3,
        train_count=1,
        validation_count=1,
        test_count=1,
        scripts=[ScriptConfig(name="Devanagari", input_path="input/devanagari.md")],
        output_dir=str(tmp_path / "seed_a"),
        seed=101,
    )
    cfg2 = DatasetConfig(
        samples_per_script=3,
        train_count=1,
        validation_count=1,
        test_count=1,
        scripts=[ScriptConfig(name="Devanagari", input_path="input/devanagari.md")],
        output_dir=str(tmp_path / "seed_b"),
        seed=202,
    )

    DatasetBuilder(config=cfg1).build()
    DatasetBuilder(config=cfg2).build()

    with open(tmp_path / "seed_a" / "manifest.json", "r", encoding="utf-8") as f1:
        data1 = json.load(f1)
    with open(tmp_path / "seed_b" / "manifest.json", "r", encoding="utf-8") as f2:
        data2 = json.load(f2)

    seeds1 = [s["seed"] for s in data1["samples"]]
    seeds2 = [s["seed"] for s in data2["samples"]]
    assert seeds1 != seeds2


def test_small_dataset_generation_summary_formatting(devanagari_only_config: DatasetConfig) -> None:
    """Test summary formatting output string."""
    builder = DatasetBuilder(config=devanagari_only_config)
    summary = builder.build()
    formatted = summary.format_summary()

    assert "Dataset generation complete" in formatted
    assert "Devanagari:" in formatted
    assert "train: 1" in formatted
    assert "validation: 1" in formatted
    assert "test: 1" in formatted
    assert "Total images: 3" in formatted
    assert "Total annotations: 3" in formatted


def test_all_three_scripts_small_dataset_generation(tmp_path: Path) -> None:
    """Test full multi-script generation across all 3 scripts (Devanagari, Modi, Sharada)."""
    cfg = DatasetConfig(
        samples_per_script=3,
        train_count=1,
        validation_count=1,
        test_count=1,
        output_dir=str(tmp_path / "all_scripts_dataset"),
        seed=42,
    )
    builder = DatasetBuilder(config=cfg)
    summary = builder.build()

    assert summary.total_images == 9
    assert summary.total_annotations == 9
    assert "Devanagari" in summary.script_counts
    assert "Modi" in summary.script_counts
    assert "Sharada" in summary.script_counts

    for sname in ("devanagari", "modi", "sharada"):
        s_dir = tmp_path / "all_scripts_dataset" / sname
        for split in ("train", "validation", "test"):
            pngs = list((s_dir / split).glob("*.png"))
            mds = list((s_dir / split).glob("*.md"))
            assert len(pngs) == 1
            assert len(mds) == 1
