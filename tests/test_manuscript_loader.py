"""Unit tests for ManuscriptLoader and Manuscript representation."""

from pathlib import Path
import pytest

from src.input.manuscript_loader import Manuscript, ManuscriptLoader


def test_load_valid_markdown(tmp_path: Path) -> None:
    """Test loading a standard valid markdown manuscript."""
    md_file = tmp_path / "valid.md"
    content = "# Chapter 1\n\nFirst paragraph content.\n\nSecond paragraph content."
    md_file.write_text(content, encoding="utf-8")

    manuscript = ManuscriptLoader.load(md_file)
    assert isinstance(manuscript, Manuscript)
    assert manuscript.source_path == md_file
    assert manuscript.character_count == len(content)
    assert manuscript.paragraph_count == 3
    assert manuscript.paragraphs[0] == "# Chapter 1"
    assert manuscript.paragraphs[1] == "First paragraph content."
    assert manuscript.paragraphs[2] == "Second paragraph content."
    assert manuscript.word_count > 0


def test_load_missing_file_raises_error(tmp_path: Path) -> None:
    """Test that attempting to load a missing file raises FileNotFoundError."""
    missing = tmp_path / "does_not_exist.md"
    with pytest.raises(FileNotFoundError, match="Manuscript file not found"):
        ManuscriptLoader.load(missing)


def test_load_directory_raises_error(tmp_path: Path) -> None:
    """Test that passing a directory path raises ValueError."""
    with pytest.raises(ValueError, match="not a regular file"):
        ManuscriptLoader.load(tmp_path)


def test_load_empty_manuscript(tmp_path: Path) -> None:
    """Test loading an empty manuscript file."""
    empty_file = tmp_path / "empty.md"
    empty_file.write_text("", encoding="utf-8")

    manuscript = ManuscriptLoader.load(empty_file)
    assert manuscript.raw_text == ""
    assert manuscript.character_count == 0
    assert manuscript.word_count == 0
    assert manuscript.paragraphs == []
    assert manuscript.paragraph_count == 0


def test_load_whitespace_only_manuscript(tmp_path: Path) -> None:
    """Test loading a manuscript with only whitespace."""
    ws_file = tmp_path / "whitespace.md"
    ws_file.write_text("   \n\n\t  \n  ", encoding="utf-8")

    manuscript = ManuscriptLoader.load(ws_file)
    assert manuscript.paragraphs == []
    assert manuscript.paragraph_count == 0


def test_safe_normalization_crlf_and_bom(tmp_path: Path) -> None:
    """Test that BOM is removed and CRLF is converted to LF."""
    bom_file = tmp_path / "bom.md"
    # Write with UTF-8 sig to include BOM and CRLF line breaks
    text_with_crlf = "\ufeffLine 1\r\n\r\nLine 2\r\n"
    bom_file.write_bytes(text_with_crlf.encode("utf-8"))

    manuscript = ManuscriptLoader.load(bom_file)
    assert not manuscript.raw_text.startswith("\ufeff")
    assert "\r\n" not in manuscript.raw_text
    assert len(manuscript.paragraphs) == 2
    assert manuscript.paragraphs[0] == "Line 1"
    assert manuscript.paragraphs[1] == "Line 2"


def test_indic_unicode_preservation(tmp_path: Path) -> None:
    """Test loading Indic text in Devanagari script."""
    indic_file = tmp_path / "indic.md"
    content = "ॐ श्री गणेशाय नमः ।\n\nअथ प्रथमोऽध्यायः ॥"
    indic_file.write_text(content, encoding="utf-8")

    manuscript = ManuscriptLoader.load(indic_file)
    assert manuscript.paragraph_count == 2
    assert manuscript.paragraphs[0] == "ॐ श्री गणेशाय नमः ।"
    assert manuscript.paragraphs[1] == "अथ प्रथमोऽध्यायः ॥"
