# Fonts Directory

Place compatible Unicode TrueType/OpenType Indic fonts (`.ttf`, `.otf`, `.ttc`) here for Devanagari, Modi, and Sharada scripts.

### Recommended Free & Open Source Fonts
- **Devanagari**:
  - [Google Noto Sans Devanagari](https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari) (OFL)
  - [Google Noto Serif Devanagari](https://fonts.google.com/noto/specimen/Noto+Serif+Devanagari) (OFL)
- **Modi**:
  - [Google Noto Sans Modi](https://fonts.google.com/noto/specimen/Noto+Sans+Modi) (OFL)
- **Sharada**:
  - [Google Noto Sans Sharada](https://fonts.google.com/noto/specimen/Noto+Sans+Sharada) (OFL)

### Font Discovery & Configuration
The manuscript generator automatically detects fonts placed in this directory, checks system Indic fonts (such as `Nirmala.ttc` on Windows), or accepts an explicit font path via CLI:
```bash
python generate.py --input input/example.md --output output/ --font assets/fonts/YourFont.ttf
```
