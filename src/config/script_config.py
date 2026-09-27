"""Script and Dataset configuration and resolution utilities."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class ScriptConfig:
    """Configuration for a specific manuscript script and typography."""

    name: str  # "Devanagari", "Modi", "Sharada"
    font_path: Optional[str] = None
    input_path: Optional[str] = None
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Script name cannot be empty")


def get_default_scripts() -> List[ScriptConfig]:
    """Return default configurations for supported manuscript scripts."""
    return [
        ScriptConfig(
            name="Devanagari",
            input_path="input/devanagari.md",
            enabled=True,
        ),
        ScriptConfig(
            name="Modi",
            input_path="input/modi.md",
            enabled=True,
        ),
        ScriptConfig(
            name="Sharada",
            input_path="input/sharada.md",
            enabled=True,
        ),
    ]


def resolve_script_font(script_name: str, configured_font_path: Optional[str] = None) -> str:
    """Resolve an authentic font path for a given manuscript script.

    Args:
        script_name: Name of the script ("Devanagari", "Modi", "Sharada").
        configured_font_path: Optional explicit font path.

    Returns:
        Absolute or relative path to the resolved font file.

    Raises:
        FileNotFoundError: If the font cannot be found. Silently falling back
            to fonts of other scripts is strictly prohibited.
    """
    script_normalized = script_name.strip()
    script_lower = script_normalized.lower()

    # 1. Explicit configured font path
    if configured_font_path:
        p = Path(configured_font_path)
        if p.is_file():
            return str(p)
        raise FileNotFoundError(
            f"{script_normalized} font '{configured_font_path}' not found."
        )

    # 2. Check dedicated script directory: assets/fonts/<script>/
    base_assets = Path("assets/fonts") / script_lower
    if base_assets.is_dir():
        for ext in ("*.ttf", "*.otf", "*.ttc"):
            matches = list(base_assets.glob(ext))
            if matches:
                return str(matches[0])

    # 3. Script-specific discovery
    if script_lower == "devanagari":
        # Check assets/fonts directly for any devanagari font
        if Path("assets/fonts").is_dir():
            for ext in ("*.ttf", "*.otf", "*.ttc"):
                for font_candidate in Path("assets/fonts").glob(ext):
                    if "devanagari" in font_candidate.name.lower():
                        return str(font_candidate)

        # Check system Indic fonts (e.g. Windows Nirmala UI / Nirmala.ttc)
        windows_font = Path(r"C:\Windows\Fonts\Nirmala.ttc")
        if windows_font.is_file():
            return str(windows_font)
        windows_font_ttf = Path(r"C:\Windows\Fonts\nirmala.ttf")
        if windows_font_ttf.is_file():
            return str(windows_font_ttf)

        # Linux common paths
        linux_candidates = [
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "/usr/share/fonts/opentype/noto/NotoSerifDevanagari-Regular.otf",
            "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        ]
        for cand in linux_candidates:
            if Path(cand).is_file():
                return cand

        raise FileNotFoundError(
            "Devanagari font not found. Configure script font path in settings.py or "
            "place the required font in assets/fonts/devanagari/."
        )

    # For Modi and Sharada: strict script-specific checking.
    # NEVER fall back to Devanagari or other script fonts!
    raise FileNotFoundError(
        f"{script_normalized} font not found. Configure script font path in settings.py or "
        f"place the required font in assets/fonts/{script_lower}/."
    )


def resolve_script_input(script_name: str, configured_input_path: Optional[str] = None) -> str:
    """Resolve manuscript markdown input file for a given script.

    Args:
        script_name: Name of the script ("Devanagari", "Modi", "Sharada").
        configured_input_path: Optional explicit input path.

    Returns:
        Path to the resolved markdown manuscript file.

    Raises:
        FileNotFoundError: If the input file cannot be found.
    """
    script_normalized = script_name.strip()
    script_lower = script_normalized.lower()

    if configured_input_path:
        p = Path(configured_input_path)
        if p.is_file():
            return str(p)
        raise FileNotFoundError(
            f"Manuscript input for {script_normalized} '{configured_input_path}' not found."
        )

    # Check input/<script>.md
    candidate = Path("input") / f"{script_lower}.md"
    if candidate.is_file():
        return str(candidate)

    # For Devanagari, allow fallback to input/example.md for backward compatibility
    if script_lower == "devanagari":
        example = Path("input/example.md")
        if example.is_file():
            return str(example)

    raise FileNotFoundError(
        f"Manuscript input for {script_normalized} not found. Place manuscript in "
        f"input/{script_lower}.md or configure input_path."
    )


@dataclass
class DatasetConfig:
    """Configuration for multi-script dataset generation and splitting."""

    samples_per_script: int = 100
    train_count: int = 85
    validation_count: int = 10
    test_count: int = 5
    scripts: List[ScriptConfig] = field(default_factory=get_default_scripts)
    output_dir: str = "dataset"
    seed: int = 42
    layouts: Tuple[str, ...] = ("traditional_single", "side_annotation", "multi_block")

    def __post_init__(self) -> None:
        if self.samples_per_script <= 0:
            raise ValueError(
                f"samples_per_script must be positive, got {self.samples_per_script}"
            )
        if self.train_count < 0 or self.validation_count < 0 or self.test_count < 0:
            raise ValueError("Split counts (train, validation, test) cannot be negative")
        total_split = self.train_count + self.validation_count + self.test_count
        if total_split != self.samples_per_script:
            raise ValueError(
                f"Split counts (train={self.train_count}, validation={self.validation_count}, "
                f"test={self.test_count}, total={total_split}) must equal "
                f"samples_per_script ({self.samples_per_script})"
            )
        if not self.scripts:
            raise ValueError("At least one script must be configured in DatasetConfig")
