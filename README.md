# Synthetic Manuscript Generator

A modular, extensible Python pipeline designed to generate visually varied synthetic historical manuscript folios and synchronized ground-truth Markdown annotations for historical Indic scripts, including Devanagari, Modi, and Sharada.

---

## 1. Project Overview & Objective

### Objective
The goal of this project is to build an automated, reproducible synthetic data generator capable of rendering historical Indic manuscripts along with fine-grained, synchronized structural and textual ground-truth annotations. The system is designed to simulate realistic manuscript characteristics—including varied physical degradation, aged backgrounds, complex folio layouts, and subtle scribal variations—to facilitate document analysis, layout analysis, and historical script recognition research.

### Key Capabilities
- **Multi-Script Support**: Dedicated TrueType font handling for **Devanagari**, **Modi**, and **Sharada**.
- **Generic Markdown Ingestion**: Accepts arbitrary input `.md` manuscripts with non-destructive normalization (Unicode NFC, standard LF line endings).
- **Geometric Pagination & Re-wrapping**: Geometry-driven line wrapping and page pagination respecting line heights and margins without text omission.
- **Folio Layout Engine**: Supports `traditional_single`, `side_annotation` (commentary/tika glosses with non-colliding gutter rules), and `multi_block` (divided verse sections) layouts.
- **Procedural Background Generation**: Procedural paper and palm-leaf manuscript textures with customizable fibers, aging gradients, stains, and edge variations.
- **Physical Aging & Imperfections**: Controllable mesh warping, paper folds/creases, ink bleed, stroke fading, and localized smudging.
- **Subtle Scribal Line Variation**: Organic line-start horizontal jitter, subtle baseline variation, and subpixel continuous baseline drift to reduce mechanical digital rigidity while maintaining 100% character legibility.
- **Synchronized Ground-Truth**: Deterministic, structured Markdown files capturing full text, block boundaries, font metrics, and section markers synchronized 1:1 with every generated image.
- **Automated Dataset Generation**: Configurable batch generator with deterministic seeding and reproducible train/validation/test splits.

---

## 2. Generic Input Workflow

The pipeline processes input manuscripts through seven decoupled stages:

```text
Arbitrary .md Input
        ↓
1. Normalization & Ingestion (ManuscriptLoader)
        ↓
2. Script & Font Resolution (ScriptConfig & TrueType fonts)
        ↓
3. Geometry & Line-Break Pagination (PageBuilder)
        ↓
4. Folio Layout Composition (LayoutEngine)
        ↓
5. Typography & Scribal Rendering (ManuscriptRenderer)
        ↓
6. Physical Effects & Aging (ManuscriptEffects & BackgroundGenerator)
        ↓
Output: PNG Folio Image (1200×800) + Synchronized Markdown (.md)
```

---

## 3. Architecture & Repository Structure

```text
synthetic-manuscript-generator/
├── generate.py                 # CLI orchestrator entry point
├── requirements.txt            # Core dependencies
├── src/
│   ├── config/
│   │   ├── settings.py         # Dataclasses for Page, Layout, Background, Effects
│   │   └── script_config.py   # Multi-script dataset configurations & font resolvers
│   ├── input/
│   │   └── manuscript_loader.py # Markdown loader with Unicode NFC normalization
│   ├── pagination/
│   │   └── page_builder.py     # Geometry-driven text measurement & line-wrapping
│   ├── layout/
│   │   └── layout_engine.py    # Layout structures (single, side annotation, multi-block)
│   ├── background/
│   │   └── background_generator.py # Procedural paper & palm leaf background synthesis
│   ├── rendering/
│   │   └── text_renderer.py    # TrueType text rendering with scribal line variation
│   ├── effects/
│   │   └── manuscript_effects.py # Mesh warping, folds, ink fading, bleed, smudges
│   ├── annotation/
│   │   └── annotation_generator.py # Structured Markdown ground-truth synchronization
│   └── dataset/
│       └── dataset_builder.py  # Batch multi-script dataset generator & manifest writer
├── assets/
│   └── fonts/                  # Authentic TrueType fonts
│       ├── devanagari/         # NotoSansDevanagari-Regular.ttf
│       ├── modi/               # NotoSansModi-Regular.ttf
│       └── sharada/            # NotoSansSharada-Regular.ttf
├── input/                      # Normalized manuscript source texts
├── output/                     # Default output directory for generated folios & datasets
└── tests/                      # Comprehensive pytest test suite (76 tests)
```

---

## 4. Installation & Dependencies

### Prerequisites
- Python 3.10+ (tested on Python 3.11)

### Setup
```bash
# Clone the repository
git clone https://github.com/shivampatle2004/synthetic-manuscript-generator.git
cd synthetic-manuscript-generator

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies
- `Pillow>=10.0.0`: Typography rendering, image compositing, and font metrics
- `numpy>=1.24.0`: Procedural noise, array manipulation, and geometric mesh grids
- `scipy>=1.10.0`: Subpixel coordinate mapping for organic scribal line undulation
- `pyyaml>=6.0`: Configuration serialisation
- `pytest>=7.4.0`: Automated unit and integration testing

---

## 5. Usage & CLI Syntax

The pipeline is operated via `generate.py` in either single-manuscript or dataset-generation mode.

### 5.1 Single Manuscript Generation
To render an arbitrary input markdown file into synthetic manuscript folios with an explicit script:

```bash
python generate.py --input input/devanagari.md --script Devanagari --output output/single_run
```

#### Additional Options for Single Generation:
- `--script`: Target script (`Devanagari`, `Modi`, `Sharada`; default: `Devanagari`)
- `--font`: Path to custom TrueType/OpenType font file
- `--layout`: Layout style (`traditional_single`, `side_annotation`, `multi_block`; default: `traditional_single`)
- `--background`: Material type (`paper`, `palm_leaf`; default: `paper`)
- `--seed`: Integer seed for deterministic generation
- `--highlight`: Enable pigment wash highlight on key passages
- `--scribal-variation`: Enable organic scribal line jitter and baseline undulation
- `--scribal-strength`: Intensity scaling for scribal line variation (0.0 to 2.0; default: 0.6)
- `--effects-strength`: Intensity scaling for physical effects (0.0 to 2.0; default: 0.3)
- `--no-effects`: Disable physical manuscript degradation effects

Example with side-annotation layout, palm-leaf background, and scribal variation:
```bash
python generate.py --input input/modi.md --script Modi --layout side_annotation --background palm_leaf --scribal-variation --output output/custom_folio
```

---

### 5.2 Multi-Script Dataset Generation

To generate the complete 300-sample multi-script dataset across Devanagari, Modi, and Sharada with exact 85/10/5 splits:

```bash
python generate.py --dataset --dataset-output output/dataset --samples-per-script 100 --dataset-seed 42
```

---

## 6. Dataset Structure & Output Specification

### Split Breakdown
The dataset generator produces exactly 300 folios divided evenly across the three scripts:

| Script | Train | Validation | Test | Total Images | Total Annotations |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Devanagari** | 85 | 10 | 5 | 100 | 100 |
| **Modi** | 85 | 10 | 5 | 100 | 100 |
| **Sharada** | 85 | 10 | 5 | 100 | 100 |
| **TOTAL** | **255** | **30** | **15** | **300 PNG** | **300 MD** |

### Output Directory Structure
```text
output/dataset/
├── manifest.json                 # Master metadata index covering all 300 samples
├── devanagari/
│   ├── train/
│   │   ├── Image_001.png
│   │   ├── Image_001.md
│   │   └── ...
│   ├── validation/
│   └── test/
├── modi/
│   ├── train/
│   ├── validation/
│   └── test/
└── sharada/
    ├── train/
    ├── validation/
    └── test/
```

### Image Format
- **Dimensions**: 1200 × 800 pixels
- **Color Mode**: 24-bit RGB PNG
- **Characteristics**: Varied aging tones, edge decay, fiber noise, folds, ink bleeding, and subtle line undulation

### Ground-Truth Annotation Format (.md)
Every `.png` file has a matching `.md` file structured as follows:

```markdown
# Manuscript Page

## Metadata

- Image: Image_001.png
- Page: 1
- Script: Devanagari
- Layout: traditional_single
- Dimensions: 1200x800

## Main Text

[Full raw Unicode text rendered in primary blocks]

## Blocks

### Block: main_text

- Block ID: page_1_main
- Role: main_text
- Position: x=80, y=60
- Size: width=1040, height=620
- Font Size: 24
- Line Height: 44
- Highlighted: false

Text:

[Exact lines of text in this block]

## Section Markers

- Marker ID: marker_top_1
  Type: lotus
  Position: x=570, y=32
  Size: width=60, height=16

## Highlights

None
```

---

## 7. Configurable Pipeline Parameters

| Module | Parameter | Type | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| **PageConfig** | `page_width` | int | 1200 | Total image width in pixels |
| | `page_height` | int | 800 | Total image height in pixels |
| | `font_size` | int | 24 | Base point size for main body text |
| | `line_spacing` | float | 1.8 | Line spacing multiplier relative to font size |
| **LayoutConfig** | `layout_style` | str | `traditional_single` | Folio layout (`traditional_single`, `side_annotation`, `multi_block`) |
| | `section_markers_enabled` | bool | True | Render ornamental chapter/verse dividers |
| | `highlights_enabled` | bool | False | Apply historical turmeric/pigment wash highlight |
| **BackgroundConfig** | `background_type` | str | `paper` | Surface texture material (`paper`, `palm_leaf`) |
| | `texture_strength` | float | 0.5 | Micro-fiber noise intensity |
| | `aging_strength` | float | 0.4 | Vignette and border oxidation intensity |
| | `stain_strength` | float | 0.3 | Watermark and moisture stain intensity |
| **EffectsConfig** | `enabled` | bool | True | Toggle physical artifact pipeline |
| | `warp_strength` | float | 0.3 | 2D mesh perspective and page curvature |
| | `fold_strength` | float | 0.3 | Crease shadow and highlight intensity |
| | `fold_count` | int | 1 | Number of vertical/horizontal folds |
| | `ink_bleed_strength` | float | 0.3 | Gaussian ink bleeding into surface fibers |
| | `fade_strength` | float | 0.3 | Stroke degradation and uneven ink deposition |
| | `smudge_strength` | float | 0.2 | Localized ink smudges |
| | `enable_scribal_variation` | bool | False | Subtle organic scribal jitter and undulation |
| | `scribal_variation_strength`| float | 0.0 | Intensity of line jitter and baseline drift |

---

## 8. Verification & Testing

The repository includes a comprehensive test suite covering input normalization, pagination, layout collision prevention, rendering, background synthesis, physical effects, ground-truth synchronization, and dataset generation:

```bash
python -m pytest -v
```

### Current Test Suite Result:
```text
======================= 76 passed in 123.68s =======================
```
- **Passed**: 76 / 76 tests (100% pass rate)
- **Coverage**: All functional pipeline modules validated

---

## 9. Repository & Distribution Information

- **GitHub Repository**: [https://github.com/shivampatle2004/synthetic-manuscript-generator](https://github.com/shivampatle2004/synthetic-manuscript-generator)
- **Hugging Face Dataset (Placeholder)**: When published, the 300-sample dataset will be accessible via:
  ```text
  https://huggingface.co/datasets/shivampatle2004/synthetic-indic-manuscripts
  ```
  *(To upload: authenticate with `huggingface-cli login`, initialize a dataset repository, and push the `output/dataset/` folder containing images, annotations, and `manifest.json`.)*
