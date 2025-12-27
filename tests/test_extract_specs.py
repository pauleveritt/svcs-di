"""Tests for spec and product metadata extraction."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from extract_specs import (  # noqa: E402  # type: ignore[import-not-found]
    discover_spec_directories,
    extract_product_metadata,
    extract_spec_metadata,
    extract_spec_summary,
    extract_spec_title,
    get_all_product_metadata,
    get_all_spec_metadata,
)


def test_discover_spec_directories():
    """Test spec directory discovery with date prefix pattern."""
    project_root = Path(__file__).parent.parent
    specs_dir = project_root / "agent-os" / "specs"

    directories = discover_spec_directories(specs_dir)

    # Should find multiple directories
    assert len(directories) > 0

    # All should have date prefix pattern
    for dir_path in directories:
        assert dir_path.name[:10].count("-") == 2  # YYYY-MM-DD format

    # Should be sorted chronologically
    dir_names = [d.name for d in directories]
    assert dir_names == sorted(dir_names)


def test_discover_spec_directories_with_exclusion():
    """Test spec directory discovery excludes specified directory."""
    project_root = Path(__file__).parent.parent
    specs_dir = project_root / "agent-os" / "specs"

    exclude_name = "2025-12-27-specifications-into-sphinx"
    directories = discover_spec_directories(specs_dir, exclude_dir=exclude_name)

    # Should not include excluded directory
    dir_names = [d.name for d in directories]
    assert exclude_name not in dir_names


def test_extract_spec_title():
    """Test title extraction from spec.md."""
    content = """# Specification: Basic Examples and Documentation

## Goal
Create comprehensive documentation.
"""
    title = extract_spec_title(content)
    assert title == "Basic Examples and Documentation"


def test_extract_spec_summary():
    """Test summary extraction from Goal section."""
    content = """# Specification: Test Spec

## Goal
Create comprehensive documentation for all 5 existing examples in `/examples/`, including inline code snippets tested with Sybil, structured by complexity, and expanded test coverage in a single test file.

## User Stories
- As a developer...
"""
    summary = extract_spec_summary(content)

    # Should extract Goal section content
    assert "comprehensive documentation" in summary
    assert "User Stories" not in summary


def test_extract_spec_metadata():
    """Test full spec metadata extraction."""
    project_root = Path(__file__).parent.parent
    specs_dir = project_root / "agent-os" / "specs"
    base_path = project_root / "docs"

    # Get first spec directory
    directories = discover_spec_directories(specs_dir)
    assert len(directories) > 0

    first_spec = directories[0]
    metadata = extract_spec_metadata(first_spec, base_path)

    # Should have all fields populated
    assert metadata.directory
    assert metadata.title
    assert metadata.summary
    assert metadata.relative_path.startswith("features/")
    assert metadata.relative_path.endswith(".md")


def test_extract_product_metadata():
    """Test product file metadata extraction."""
    project_root = Path(__file__).parent.parent
    product_dir = project_root / "agent-os" / "product"
    base_path = project_root / "docs"

    mission_file = product_dir / "mission.md"
    metadata = extract_product_metadata(mission_file, base_path)

    # Should extract title and summary
    assert metadata.title == "Product Mission"
    assert "dependency injection" in metadata.summary.lower()
    assert metadata.relative_path == "product/mission.md"


def test_get_all_spec_metadata():
    """Test getting all spec metadata."""
    project_root = Path(__file__).parent.parent
    specs_dir = project_root / "agent-os" / "specs"
    base_path = project_root / "docs"

    all_metadata = get_all_spec_metadata(
        specs_dir, base_path, exclude_dir="2025-12-27-specifications-into-sphinx"
    )

    # Should return multiple specs
    assert len(all_metadata) > 0

    # All should have required fields
    for metadata in all_metadata:
        assert metadata.directory
        assert metadata.title
        assert metadata.summary
        assert metadata.relative_path


def test_get_all_product_metadata():
    """Test getting all product metadata in correct order."""
    project_root = Path(__file__).parent.parent
    product_dir = project_root / "agent-os" / "product"
    base_path = project_root / "docs"

    all_metadata = get_all_product_metadata(product_dir, base_path)

    # Should return 3 files in order
    assert len(all_metadata) == 3

    filenames = [m.filename for m in all_metadata]
    assert filenames == ["mission.md", "roadmap.md", "tech-stack.md"]

    # All should have summaries
    for metadata in all_metadata:
        assert metadata.title
        assert metadata.summary
        assert len(metadata.summary) > 0
