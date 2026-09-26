# Synthetic Manuscript Generator

A modular pipeline for generating synthetic historical manuscript images and synchronized Markdown ground-truth annotations for historical Indic scripts, including Devanagari, Modi, and Sharada.

## Overview

This repository provides a reusable and extensible framework designed to simulate realistic historical manuscripts along with exact corresponding textual and structural annotations.

### Planned Capabilities
- **Script Support**: Devanagari, Modi, and Sharada.
- **Image Generation**: Synthetic historical manuscript pages with authentic paper/palm-leaf textures, deterioration, and physical aging effects.
- **Ground-Truth Synchronization**: Synchronized Markdown annotations paired with generated page layouts.
- **Modular Pipeline**: Clean separation of input processing, pagination, layout composition, background textures, rendering, degradation effects, annotation generation, and dataset export.

## Project Structure

```
synthetic-manuscript-generator/
├── generate.py          # Orchestrator and CLI entry point
├── requirements.txt     # Project dependencies
├── src/
│   ├── config/          # Pipeline configuration
│   ├── input/           # Input text processing and ingestion
│   ├── pagination/      # Text pagination and line breaking
│   ├── layout/          # Page layout and bounding geometry
│   ├── background/      # Manuscript surface and background generation
│   ├── rendering/       # Typography and script rendering
│   ├── effects/         # Aging, deterioration, and degradation effects
│   ├── annotation/      # Ground-truth Markdown and metadata generation
│   └── dataset/         # Dataset export and packaging
├── input/               # Input corpus files and source assets
├── output/              # Generated manuscript images and annotations
└── tests/               # Unit and integration test suites
```

## Getting Started

1. Set up a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the generation pipeline:
   ```bash
   python generate.py
   ```
