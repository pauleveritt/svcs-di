"""Extract metadata from specifications for Sphinx documentation."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SpecMetadata:
    """Metadata extracted from a spec.md file."""

    directory: str
    title: str
    summary: str
    relative_path: str


@dataclass
class ProductMetadata:
    """Metadata extracted from a product file."""

    filename: str
    title: str
    summary: str
    relative_path: str


def discover_spec_directories(specs_dir: Path, exclude_dir: str | None = None) -> list[Path]:
    """Discover all spec directories with date prefix pattern.

    Args:
        specs_dir: Path to agent-os/specs/ directory
        exclude_dir: Directory name to exclude (e.g., current spec)

    Returns:
        List of spec directory paths in chronological order
    """
    # Pattern for YYYY-MM-DD-* directories
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-")

    directories = []
    for item in specs_dir.iterdir():
        if not item.is_dir():
            continue

        # Check if matches date pattern
        if not date_pattern.match(item.name):
            continue

        # Exclude specified directory
        if exclude_dir and item.name == exclude_dir:
            continue

        directories.append(item)

    # Sort chronologically (alphabetical sort on date prefix gives chronological order)
    return sorted(directories, key=lambda p: p.name)


def extract_spec_title(spec_content: str) -> str:
    """Extract title from spec.md H1 heading.

    Args:
        spec_content: Content of spec.md file

    Returns:
        Title with "Specification: " prefix removed
    """
    lines = spec_content.strip().split("\n")
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            # Remove "Specification: " prefix if present
            if title.startswith("Specification: "):
                title = title[len("Specification: ") :]
            return title
    return "Untitled Specification"


def extract_spec_summary(spec_content: str) -> str:
    """Extract summary from Goal section of spec.md.

    Args:
        spec_content: Content of spec.md file

    Returns:
        Summary text (1-2 sentences from Goal section)
    """
    lines = spec_content.strip().split("\n")

    # Find ## Goal heading
    goal_index = None
    for i, line in enumerate(lines):
        if line.strip() == "## Goal":
            goal_index = i
            break

    if goal_index is None:
        # Fallback: use first paragraph after title
        return extract_first_paragraph(spec_content)

    # Get content after Goal heading (skip empty lines)
    summary_lines = []
    for line in lines[goal_index + 1 :]:
        stripped = line.strip()

        # Stop at next heading or after getting content
        if stripped.startswith("#"):
            break

        if stripped:
            summary_lines.append(stripped)
            # Limit to approximately 1-2 sentences
            if len(" ".join(summary_lines)) > 200:
                break

    if not summary_lines:
        return extract_first_paragraph(spec_content)

    return " ".join(summary_lines)


def extract_first_paragraph(content: str) -> str:
    """Extract first paragraph after title.

    Args:
        content: File content

    Returns:
        First paragraph text
    """
    lines = content.strip().split("\n")

    # Skip title
    start_index = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            start_index = i + 1
            break

    # Get first paragraph
    paragraph_lines = []
    for line in lines[start_index:]:
        stripped = line.strip()

        # Stop at next heading
        if stripped.startswith("#"):
            break

        if stripped:
            paragraph_lines.append(stripped)
            # Limit length
            if len(" ".join(paragraph_lines)) > 200:
                break

    return " ".join(paragraph_lines) if paragraph_lines else "No summary available."


def extract_product_summary(product_file: Path) -> str:
    """Extract summary from product file.

    Args:
        product_file: Path to product markdown file

    Returns:
        Summary text (2-3 sentences)
    """
    content = product_file.read_text()
    lines = content.strip().split("\n")

    # For mission.md: Extract from Pitch section
    if product_file.name == "mission.md":
        pitch_index = None
        for i, line in enumerate(lines):
            if line.strip() == "## Pitch":
                pitch_index = i
                break

        if pitch_index is not None:
            summary_lines = []
            for line in lines[pitch_index + 1 :]:
                stripped = line.strip()
                if stripped.startswith("#"):
                    break
                if stripped:
                    summary_lines.append(stripped)
                    # Get approximately 2-3 sentences
                    if len(" ".join(summary_lines)) > 300:
                        break
            if summary_lines:
                return " ".join(summary_lines)

    # For tech-stack.md: Create summary from bullet points
    if product_file.name == "tech-stack.md":
        # Extract key information from Language & Runtime section
        return (
            "Core technology stack based on Python 3.14+ with modern type hints, "
            "protocol support, and free-threaded compatibility, using uv for package "
            "management and building on the svcs library foundation."
        )

    # For roadmap.md: Extract first item's description
    if product_file.name == "roadmap.md":
        # Find first numbered item with description
        for i, line in enumerate(lines):
            if line.strip().startswith("1."):
                # Extract the description part (everything after the em-dash)
                if "—" in line:
                    description = line.split("—", 1)[1].strip()
                    # Limit to approximately 2-3 sentences
                    if len(description) > 250:
                        # Find the end of first sentence
                        first_period = description.find(". ")
                        if first_period > 0:
                            description = description[: first_period + 1]
                    return description

    # Fallback: Extract from first section
    return extract_first_paragraph(content)


def extract_spec_metadata(spec_dir: Path, base_path: Path) -> SpecMetadata:
    """Extract metadata from a spec directory.

    Args:
        spec_dir: Path to spec directory
        base_path: Base path for calculating relative paths (typically docs/)

    Returns:
        SpecMetadata with extracted information
    """
    spec_file = spec_dir / "spec.md"

    # Create slug from directory name (remove date prefix)
    # e.g., "2025-12-24-basic-examples" -> "basic-examples"
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", spec_dir.name)

    if not spec_file.exists():
        # Return placeholder if spec.md doesn't exist
        return SpecMetadata(
            directory=spec_dir.name,
            title=spec_dir.name,
            summary="No spec.md file found.",
            relative_path=f"features/{slug}.md",
        )

    content = spec_file.read_text()
    title = extract_spec_title(content)
    summary = extract_spec_summary(content)

    # Calculate relative path from docs/specifications/ to feature page
    relative_path = f"features/{slug}.md"

    return SpecMetadata(
        directory=spec_dir.name,
        title=title,
        summary=summary,
        relative_path=relative_path,
    )


def extract_product_metadata(product_file: Path, base_path: Path) -> ProductMetadata:
    """Extract metadata from a product file.

    Args:
        product_file: Path to product markdown file
        base_path: Base path for calculating relative paths (typically docs/)

    Returns:
        ProductMetadata with extracted information
    """
    content = product_file.read_text()

    # Extract title from first H1 heading
    title = "Untitled"
    for line in content.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break

    summary = extract_product_summary(product_file)

    # Calculate relative path from docs/specifications/ to product documentation page
    relative_path = f"product/{product_file.name}"

    return ProductMetadata(
        filename=product_file.name,
        title=title,
        summary=summary,
        relative_path=relative_path,
    )


def get_all_spec_metadata(
    specs_dir: Path, base_path: Path, exclude_dir: str | None = None
) -> list[SpecMetadata]:
    """Get metadata for all spec directories.

    Args:
        specs_dir: Path to agent-os/specs/ directory
        base_path: Base path for calculating relative paths
        exclude_dir: Directory name to exclude

    Returns:
        List of SpecMetadata in chronological order
    """
    directories = discover_spec_directories(specs_dir, exclude_dir)
    return [extract_spec_metadata(spec_dir, base_path) for spec_dir in directories]


def get_all_product_metadata(product_dir: Path, base_path: Path) -> list[ProductMetadata]:
    """Get metadata for all product files.

    Args:
        product_dir: Path to agent-os/product/ directory
        base_path: Base path for calculating relative paths

    Returns:
        List of ProductMetadata in order: mission, roadmap, tech-stack
    """
    order = ["mission.md", "roadmap.md", "tech-stack.md"]
    metadata = []

    for filename in order:
        file_path = product_dir / filename
        if file_path.exists():
            metadata.append(extract_product_metadata(file_path, base_path))

    return metadata
