# Specs Into Sphinx Standards

## Purpose

This skill documents the pattern for integrating product documentation and feature specifications from an `agent-os/` directory structure into Sphinx documentation, creating a browsable "Specifications" section that provides access to project mission, roadmap, technical stack, and chronologically-ordered feature specifications.

**Key Implementation Approach:**
- Source files remain in `agent-os/` directory (outside Sphinx source tree)
- Create wrapper pages inside `docs/specifications/` using MyST `{include}` directives
- Wrapper pages embed source content, making it part of the Sphinx build
- Landing page links to wrapper pages (not raw source files)
- This ensures proper navigation, styling, and integration with Sphinx documentation

## When to Use

Use this skill when you need to:

- Integrate specification documents from outside the Sphinx source tree into published documentation
- Create a landing page that summarizes and links to multiple external markdown documents
- Automatically discover and order specifications based on directory naming patterns
- Extract metadata (titles, summaries) from markdown files for display in documentation
- Maintain a chronological view of feature development through specifications

## Key Patterns

### Directory Discovery

Discover specification directories using a date prefix pattern:

```python
import re
from pathlib import Path

def discover_spec_directories(specs_dir: Path, exclude_dir: str | None = None) -> list[Path]:
    """Discover all spec directories with YYYY-MM-DD-* pattern."""
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-")

    directories = []
    for item in specs_dir.iterdir():
        if not item.is_dir():
            continue
        if not date_pattern.match(item.name):
            continue
        if exclude_dir and item.name == exclude_dir:
            continue
        directories.append(item)

    # Alphabetical sort gives chronological order
    return sorted(directories, key=lambda p: p.name)
```

**Key Points:**
- Use regex pattern `^\d{4}-\d{2}-\d{2}-` to match date-prefixed directories
- Alphabetical sorting on date prefix provides chronological ordering
- Support exclusion of current/work-in-progress specifications
- Return Path objects for further processing

### Metadata Extraction

Extract titles and summaries from specification markdown files:

```python
def extract_spec_title(spec_content: str) -> str:
    """Extract title from H1 heading, removing 'Specification: ' prefix."""
    lines = spec_content.strip().split("\n")
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            if title.startswith("Specification: "):
                title = title[len("Specification: "):]
            return title
    return "Untitled Specification"

def extract_spec_summary(spec_content: str) -> str:
    """Extract summary from ## Goal section."""
    lines = spec_content.strip().split("\n")

    # Find ## Goal heading
    goal_index = None
    for i, line in enumerate(lines):
        if line.strip() == "## Goal":
            goal_index = i
            break

    if goal_index is None:
        return extract_first_paragraph(spec_content)

    # Get content after Goal heading
    summary_lines = []
    for line in lines[goal_index + 1:]:
        stripped = line.strip()
        if stripped.startswith("#"):  # Stop at next heading
            break
        if stripped:
            summary_lines.append(stripped)
            if len(" ".join(summary_lines)) > 200:  # Limit length
                break

    return " ".join(summary_lines) if summary_lines else extract_first_paragraph(spec_content)
```

**Key Points:**
- Look for standard section markers (`## Goal`) for consistent extraction
- Remove common prefixes ("Specification: ") for cleaner display
- Limit summary length to 1-2 sentences (~200 characters)
- Provide fallback to first paragraph if expected section is missing
- Handle missing or malformed files gracefully

### Product File Summaries

Handle different product documentation file formats:

```python
def extract_product_summary(product_file: Path) -> str:
    """Extract appropriate summary based on file type."""
    content = product_file.read_text()
    lines = content.strip().split("\n")

    # mission.md: Extract from Pitch section
    if product_file.name == "mission.md":
        for i, line in enumerate(lines):
            if line.strip() == "## Pitch":
                # Extract content after Pitch heading
                pass

    # tech-stack.md: Create descriptive summary from structure
    if product_file.name == "tech-stack.md":
        return (
            "Core technology stack based on Python 3.14+ with modern type hints, "
            "protocol support, and free-threaded compatibility..."
        )

    # roadmap.md: Extract from first roadmap item
    if product_file.name == "roadmap.md":
        for line in lines:
            if line.strip().startswith("1."):
                # Extract description after em-dash
                if "—" in line:
                    description = line.split("—", 1)[1].strip()
                    return description

    return extract_first_paragraph(content)
```

**Key Points:**
- Different files have different structures requiring custom extraction
- Mission files typically have a "Pitch" section with concise summary
- Roadmap files use numbered lists with descriptions after em-dashes
- Tech stack files may need manual summarization due to bullet point format
- Always provide fallback extraction method

### Sphinx Integration with Include Directives

Instead of linking directly to raw markdown files outside the docs tree, create wrapper pages that use `{include}` directives to embed the content:

**Step 1: Create wrapper pages for product documentation**

**File: docs/specifications/product/mission.md**
```markdown
# Product Mission

```{include} ../../../agent-os/product/mission.md
:relative-docs: docs/
:relative-images:
```
```

**File: docs/specifications/product/roadmap.md**
```markdown
# Product Roadmap

```{include} ../../../agent-os/product/roadmap.md
:relative-docs: docs/
:relative-images:
```
```

**Step 2: Create wrapper pages for feature specifications**

**File: docs/specifications/features/basic-examples-and-documentation.md**
```markdown
```{include} ../../../agent-os/specs/2025-12-24-basic-examples-and-documentation/spec.md
:relative-docs: docs/
:relative-images:
```
```

**Step 3: Create landing page linking to wrapper pages**

**File: docs/specifications/index.md**

```markdown
# Specifications

Introductory paragraph explaining the purpose of this section.

## Product

Overview text about product documentation.

### Mission

Summary extracted from mission.md file.

[Read More](product/mission.md)

### Roadmap

Summary extracted from roadmap.md file.

[Read More](product/roadmap.md)

## Features

Overview text about feature specifications in chronological order.

### Feature Title 1

Summary extracted from spec.md Goal section.

[Read More](features/basic-examples-and-documentation.md)

### Feature Title 2

Summary extracted from spec.md Goal section.

[Read More](features/another-feature.md)
```

**Key Points:**
- Create wrapper pages with `{include}` directives instead of linking directly to external files
- This makes the content part of the Sphinx build and properly navigable
- Use `:relative-docs:` and `:relative-images:` options for proper path resolution
- "Read More" links point to wrapper pages within docs tree (`product/mission.md`, `features/feature-name.md`)
- Wrapper page filenames use slugs (date prefix removed from spec directory names)
- Each wrapper page uses MyST `{include}` directive to embed the actual content
- Structure with H2 sections (Product, Features) and H3 subsections for each item
- Provide descriptive introductory text for each major section

### Navigation Integration

Add specifications to the main documentation navigation:

**File: docs/index.md**

```markdown
```{toctree}
:maxdepth: 2
:hidden:

examples/index
core-concepts
api-reference
specifications/index
```

## Next Steps

- Explore [Examples](examples/index.md) to see svcs-di in action
- Read [Core Concepts](core-concepts.md) to understand the architecture
- Check [API Reference](api-reference.md) for detailed function documentation
- Browse [Specifications](specifications/index.md) to understand the project's mission and development history
```

**Key Points:**
- Add `specifications/index` to main toctree (without .md extension)
- Place after main documentation sections (examples, concepts, API)
- Add navigation link in "Next Steps" section with descriptive text
- Use standard toctree options (`:maxdepth: 2`, `:hidden:`)

## Automated Generation

Create scripts to automatically generate both wrapper pages and the specifications index:

**Step 1: Create wrapper pages for each source file**

For product files, create wrapper pages in `docs/specifications/product/`:
```python
def create_product_wrapper_pages(project_root: Path):
    """Create wrapper pages with {include} directives for product docs."""
    product_dir = project_root / "agent-os" / "product"
    wrapper_dir = project_root / "docs" / "specifications" / "product"
    wrapper_dir.mkdir(parents=True, exist_ok=True)

    for product_file in ["mission.md", "roadmap.md", "tech-stack.md"]:
        source_path = product_dir / product_file
        if source_path.exists():
            # Calculate relative path from wrapper to source
            relative_path = f"../../../agent-os/product/{product_file}"

            # Create wrapper with include directive
            wrapper_content = f"""# {get_title_from_file(source_path)}

```{{include}} {relative_path}
:relative-docs: docs/
:relative-images:
```
"""
            wrapper_path = wrapper_dir / product_file
            wrapper_path.write_text(wrapper_content)
```

For spec files, create wrapper pages in `docs/specifications/features/`:
```python
def create_spec_wrapper_pages(project_root: Path):
    """Create wrapper pages with {include} directives for spec docs."""
    specs_dir = project_root / "agent-os" / "specs"
    wrapper_dir = project_root / "docs" / "specifications" / "features"
    wrapper_dir.mkdir(parents=True, exist_ok=True)

    spec_dirs = discover_spec_directories(specs_dir, exclude_dir="current-spec")

    for spec_dir in spec_dirs:
        spec_file = spec_dir / "spec.md"
        if spec_file.exists():  # IMPORTANT: Skip directories without spec.md
            # Create slug from directory name (remove date prefix)
            slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", spec_dir.name)

            # Calculate relative path from wrapper to source
            relative_path = f"../../../agent-os/specs/{spec_dir.name}/spec.md"

            # Create wrapper with include directive (no title needed)
            wrapper_content = f"""```{{include}} {relative_path}
:relative-docs: docs/
:relative-images:
```
"""
            wrapper_path = wrapper_dir / f"{slug}.md"
            wrapper_path.write_text(wrapper_content)
        # else: Skip this directory - no wrapper page will be created
```

**IMPORTANT:** Only create wrapper pages for spec directories that contain a `spec.md` file. If a spec directory exists but doesn't have a `spec.md` file, skip it entirely - don't create a wrapper page. This prevents broken includes and missing content errors during the Sphinx build.

**Step 2: Generate the specifications index**

**File: scripts/generate_specs_index.py**

```python
def generate_specifications_index(project_root: Path) -> str:
    """Generate specifications/index.md content."""
    specs_dir = project_root / "agent-os" / "specs"
    product_dir = project_root / "agent-os" / "product"

    # Get metadata
    product_metadata = get_all_product_metadata(product_dir)
    spec_metadata = get_all_spec_metadata(specs_dir, exclude_dir="current-spec")

    # Build markdown content
    lines = ["# Specifications", "", "Introduction text...", ""]

    # Add product sections
    lines.extend(["## Product", "", "Overview text...", ""])
    for product in product_metadata:
        lines.extend([
            f"### {product.title}",
            "",
            product.summary,
            "",
            f"[Read More]({product.relative_path})",  # e.g., product/mission.md
            ""
        ])

    # Add feature sections
    lines.extend(["## Features", "", "Overview text...", ""])
    for spec in spec_metadata:
        lines.extend([
            f"### {spec.title}",
            "",
            spec.summary,
            "",
            f"[Read More]({spec.relative_path})",  # e.g., features/feature-name.md
            ""
        ])

    return "\n".join(lines)
```

**Update metadata extraction to return wrapper page paths:**

```python
def extract_spec_metadata(spec_dir: Path, base_path: Path) -> SpecMetadata:
    """Extract metadata and calculate path to wrapper page."""
    spec_file = spec_dir / "spec.md"

    # Create slug from directory name (remove date prefix)
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", spec_dir.name)

    if not spec_file.exists():
        return SpecMetadata(
            directory=spec_dir.name,
            title=spec_dir.name,
            summary="No spec.md file found.",
            relative_path=f"features/{slug}.md"  # Path to wrapper page
        )

    content = spec_file.read_text()
    title = extract_spec_title(content)
    summary = extract_spec_summary(content)

    # Return path to wrapper page, not source file
    return SpecMetadata(
        directory=spec_dir.name,
        title=title,
        summary=summary,
        relative_path=f"features/{slug}.md"
    )

def extract_product_metadata(product_file: Path, base_path: Path) -> ProductMetadata:
    """Extract metadata and calculate path to wrapper page."""
    content = product_file.read_text()
    title = extract_title(content)
    summary = extract_product_summary(product_file)

    # Return path to wrapper page, not source file
    return ProductMetadata(
        filename=product_file.name,
        title=title,
        summary=summary,
        relative_path=f"product/{product_file.name}"
    )
```

**Key Points:**
- Create wrapper pages first, then generate index
- Wrapper pages use `{include}` directives to embed source content
- **Skip spec directories that don't have `spec.md` files** - don't create wrapper pages for them
- Only create wrapper pages for directories with existing `spec.md` files
- Metadata extraction returns paths to wrapper pages, not source files
- Slug generation removes date prefixes from spec directory names
- Separate data extraction from content generation
- Build content as list of lines for easy manipulation
- Make scripts runnable as standalone tools for regeneration

## Testing Approach

Write focused tests for discovery and extraction logic:

```python
def test_discover_spec_directories():
    """Test spec directory discovery with date prefix pattern."""
    specs_dir = Path("agent-os/specs")
    directories = discover_spec_directories(specs_dir)

    assert len(directories) > 0
    # All should have date prefix
    for dir_path in directories:
        assert dir_path.name[:10].count("-") == 2  # YYYY-MM-DD format
    # Should be sorted chronologically
    dir_names = [d.name for d in directories]
    assert dir_names == sorted(dir_names)

def test_extract_spec_title():
    """Test title extraction removes 'Specification:' prefix."""
    content = "# Specification: Feature Name\n\n## Goal\nDescription."
    title = extract_spec_title(content)
    assert title == "Feature Name"

def test_extract_spec_summary():
    """Test summary extraction from Goal section."""
    content = "# Title\n\n## Goal\nThis is the goal.\n\n## Details\nMore info."
    summary = extract_spec_summary(content)
    assert "goal" in summary.lower()
    assert "Details" not in summary

def test_extract_spec_metadata():
    """Test metadata extraction returns wrapper page path."""
    spec_dir = Path("agent-os/specs/2024-01-15-feature-name")
    metadata = extract_spec_metadata(spec_dir, Path("docs"))

    assert metadata.title == "Feature Name"
    assert metadata.relative_path.startswith("features/")
    assert metadata.relative_path.endswith(".md")
    # Should use slug (date prefix removed)
    assert metadata.relative_path == "features/feature-name.md"

def test_extract_product_metadata():
    """Test product metadata extraction returns wrapper page path."""
    product_file = Path("agent-os/product/mission.md")
    metadata = extract_product_metadata(product_file, Path("docs"))

    assert metadata.title == "Product Mission"
    # Should point to wrapper page, not source file
    assert metadata.relative_path == "product/mission.md"
```

**Key Points:**
- Test directory discovery filters and ordering
- Test title extraction and prefix removal
- Test summary extraction from specific sections
- Test graceful handling of missing sections
- **Test that paths point to wrapper pages, not source files**
- **Test slug generation removes date prefixes**
- Keep tests focused on extraction logic, not Sphinx build

## Build Verification

Verify the Sphinx build succeeds with wrapper pages and included content:

```bash
# Build documentation
uv run sphinx-build -W -b html docs docs/_build/html

# Verify wrapper pages were built
ls docs/_build/html/specifications/product/
ls docs/_build/html/specifications/features/

# Check that all links work in the built HTML
# Open docs/_build/html/specifications/index.html in browser
```

**Key Points:**
- Build with `-W` flag to treat warnings as errors
- Wrapper pages are now part of the docs tree, so no warnings about external files
- All content from `agent-os/` is included via `{include}` directives
- Verify that HTML pages were generated for all wrapper pages
- Test navigation: clicking "Read More" should navigate to wrapper pages
- Verify included content renders correctly with proper formatting
- Check that navigation includes Specifications section with proper hierarchy

## Common Issues

### Wrapper Page Path Resolution

**Problem:** Links break because wrapper pages use wrong paths in `{include}` directives.

**Solution:** Calculate paths relative to wrapper page location:
- From `docs/specifications/product/mission.md` to source: `../../../agent-os/product/mission.md`
- From `docs/specifications/features/feature-name.md` to source: `../../../agent-os/specs/2024-01-15-feature-name/spec.md`

### Include Directive Options

**Problem:** Links or images in included content don't resolve correctly.

**Solution:** Always use `:relative-docs:` and `:relative-images:` options:
```markdown
```{include} ../../../agent-os/product/mission.md
:relative-docs: docs/
:relative-images:
```
```

### Slug Generation from Directory Names

**Problem:** Wrapper page filenames don't match URL-friendly slugs.

**Solution:** Remove date prefix when creating wrapper pages:
```python
# Convert "2024-01-15-feature-name" to "feature-name"
slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", spec_dir.name)
wrapper_path = wrapper_dir / f"{slug}.md"
```

### Link Target Paths in Index

**Problem:** Index links point to source files instead of wrapper pages.

**Solution:** Update metadata extraction to return wrapper page paths:
```python
# Old (wrong): relative_path = "../../agent-os/specs/dirname/spec.md"
# New (correct): relative_path = "features/feature-name.md"
```

### Summary Text Too Long

**Problem:** Extracted summaries are entire paragraphs instead of 1-2 sentences.

**Solution:** Implement length limits in extraction:
```python
if len(" ".join(summary_lines)) > 200:
    break
```

### Missing Spec.md Files

**Problem:** Some spec directories don't have spec.md files yet (work in progress, planning stage, etc.).

**Solution:** Handle gracefully by skipping wrapper page creation and providing placeholder metadata:

```python
def create_spec_wrapper_pages(project_root: Path):
    """Create wrapper pages only for specs with spec.md files."""
    for spec_dir in spec_dirs:
        spec_file = spec_dir / "spec.md"
        if spec_file.exists():
            # Create wrapper page
            create_wrapper(spec_dir, spec_file)
        else:
            # Skip - no wrapper page created for this directory
            continue

def extract_spec_metadata(spec_dir: Path, base_path: Path) -> SpecMetadata:
    """Extract metadata, providing placeholder if spec.md is missing."""
    spec_file = spec_dir / "spec.md"
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", spec_dir.name)

    if not spec_file.exists():
        # Return placeholder metadata (no wrapper page exists)
        return SpecMetadata(
            directory=spec_dir.name,
            title=spec_dir.name,
            summary="No spec.md file found.",
            relative_path=f"features/{slug}.md"  # Path where wrapper would be
        )

    # Extract actual metadata
    return extract_from_file(spec_file, slug)
```

**Key Points:**
- **Don't create wrapper pages** for directories without `spec.md` files
- Only directories with `spec.md` get wrapper pages in `docs/specifications/features/`
- Metadata extraction still returns placeholder info (useful for debugging)
- Index generation will show "No spec.md file found" message for missing specs
- This prevents Sphinx build errors from broken `{include}` directives
- As specs are completed and `spec.md` files are added, re-run generation to create their wrapper pages

## Reusability

This pattern is reusable for any project that needs to:

1. **Integrate external documentation** into Sphinx while keeping source files outside the docs tree
2. **Use wrapper pages with `{include}` directives** to make external content part of the Sphinx build
3. **Auto-discover directories** based on naming patterns (dates, prefixes, categories)
4. **Extract metadata** from markdown files for summary display
5. **Generate landing pages** that provide overview and navigation to detailed documents
6. **Maintain chronological views** of project evolution through dated specifications
7. **Create proper documentation navigation** without warnings about external files

The core extraction and generation logic can be adapted for different directory structures, file formats, and metadata requirements. The wrapper page approach ensures that all content is properly integrated into the Sphinx documentation system with correct navigation, styling, and cross-references.

## Example Directory Structure

```
project/
├── agent-os/
│   ├── product/
│   │   ├── mission.md          # Source files
│   │   ├── roadmap.md
│   │   └── tech-stack.md
│   └── specs/
│       ├── 2024-01-01-first-feature/
│       │   └── spec.md         # Source files
│       ├── 2024-01-15-second-feature/
│       │   └── spec.md
│       └── 2024-02-01-third-feature/
│           └── spec.md
├── docs/
│   ├── index.md
│   ├── specifications/
│   │   ├── index.md            # Landing page with summaries
│   │   ├── product/            # Wrapper pages for product docs
│   │   │   ├── mission.md
│   │   │   ├── roadmap.md
│   │   │   └── tech-stack.md
│   │   └── features/           # Wrapper pages for specs
│   │       ├── first-feature.md
│   │       ├── second-feature.md
│   │       └── third-feature.md
│   └── _build/
└── scripts/
    ├── extract_specs.py         # Metadata extraction
    └── generate_specs_index.py  # Index and wrapper generation
```

**Key Structure Points:**
- Source files remain in `agent-os/` directory
- Wrapper pages in `docs/specifications/product/` and `docs/specifications/features/`
- Wrapper pages use `{include}` directives to embed source content
- Landing page (`specifications/index.md`) links to wrapper pages
- Wrapper filenames use slugs (date prefixes removed)

## Related Skills

- **MyST Markdown**: Understanding MyST parser directives and options
- **Sphinx Configuration**: Working with Sphinx configuration and extensions
- **Metadata Extraction**: Parsing markdown files for structured information
- **Path Management**: Calculating relative paths for cross-directory references
- **Automated Documentation**: Generating documentation from code/file structures
