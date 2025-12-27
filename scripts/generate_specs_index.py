"""Generate the specifications index page for Sphinx documentation."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from extract_specs import get_all_product_metadata, get_all_spec_metadata


def generate_specifications_index(project_root: Path) -> str:
    """Generate the specifications/index.md content.

    Args:
        project_root: Root directory of the project

    Returns:
        Markdown content for the specifications index
    """
    specs_dir = project_root / "agent-os" / "specs"
    product_dir = project_root / "agent-os" / "product"
    base_path = project_root / "docs"

    # Get all metadata
    product_metadata = get_all_product_metadata(product_dir, base_path)
    spec_metadata = get_all_spec_metadata(
        specs_dir, base_path, exclude_dir="2025-12-27-specifications-into-sphinx"
    )

    # Build the markdown content
    lines = [
        "# Specifications",
        "",
        "This section provides access to the product documentation and feature specifications that guide the development of svcs-di. Here you can explore the project's mission, roadmap, technology choices, and the detailed specifications for each implemented feature.",
        "",
        "## Product",
        "",
        "Core product documentation describing the vision, goals, and technical foundation of svcs-di.",
        "",
    ]

    # Add product sections
    for product in product_metadata:
        # Create clean title (remove "Product " prefix if present)
        section_title = product.title.replace("Product ", "")

        lines.extend(
            [
                f"### {section_title}",
                "",
                product.summary,
                "",
                f"[Read More]({product.relative_path})",
                "",
            ]
        )

    # Add features section
    lines.extend(
        [
            "## Features",
            "",
            "Feature specifications documenting the evolution of svcs-di, presented in chronological order to show how the project has developed over time.",
            "",
        ]
    )

    # Add spec sections
    for spec in spec_metadata:
        lines.extend(
            [
                f"### {spec.title}",
                "",
                spec.summary,
                "",
                f"[Read More]({spec.relative_path})",
                "",
            ]
        )

    return "\n".join(lines)


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"
    specs_index_dir = docs_dir / "specifications"

    # Ensure directory exists
    specs_index_dir.mkdir(parents=True, exist_ok=True)

    # Generate content
    content = generate_specifications_index(project_root)

    # Write file
    index_file = specs_index_dir / "index.md"
    index_file.write_text(content)

    print(f"Generated {index_file}")


if __name__ == "__main__":
    main()
