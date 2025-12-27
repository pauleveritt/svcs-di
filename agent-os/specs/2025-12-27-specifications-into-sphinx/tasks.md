# Task Breakdown: Specifications Into Sphinx

## Overview
Total Tasks: 4 Task Groups

## Task List

### Discovery & Metadata Extraction

#### Task Group 1: File Discovery and Content Extraction
**Dependencies:** None

- [x] 1.0 Complete discovery and extraction logic
  - [x] 1.1 Write 2-8 focused tests for file discovery and metadata extraction
    - Limit to 2-8 highly focused tests maximum
    - Test spec directory discovery with date prefix pattern matching
    - Test title extraction from spec.md H1 heading
    - Test summary extraction from Goal section
    - Test product file summary extraction
    - Skip exhaustive coverage of edge cases
  - [x] 1.2 Implement spec directory discovery
    - Scan `agent-os/specs/` for subdirectories with `YYYY-MM-DD-*` pattern
    - Sort directories chronologically (alphabetical on date prefix)
    - Filter out current spec directory (`2025-12-27-specifications-into-sphinx`)
    - Return list of valid spec directories in chronological order
  - [x] 1.3 Implement spec metadata extraction
    - Read each `spec.md` file from discovered directories
    - Extract title from first H1 heading (remove "Specification: " prefix)
    - Extract summary from "## Goal" section (first paragraph, 1-2 sentences)
    - Handle specs without Goal section gracefully (use first paragraph after title)
    - Return structured metadata: {directory, title, summary, relative_path}
  - [x] 1.4 Implement product file summary extraction
    - Extract summary from `mission.md` Pitch section (lines 3-6 or first 2-3 sentences)
    - Extract summary from `roadmap.md` first paragraph or roadmap item
    - Extract summary from `tech-stack.md` Language & Runtime section intro
    - Limit summaries to 1-2 sentences for consistency
    - Return structured data for each product file
  - [x] 1.5 Ensure discovery and extraction tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify correct directory filtering and ordering
    - Verify accurate metadata extraction
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- All spec directories with date prefix are discovered
- Current spec directory is excluded
- Chronological ordering is correct
- Titles and summaries are extracted accurately
- Product file summaries are extracted correctly

### Documentation Structure

#### Task Group 2: Sphinx Documentation Files
**Dependencies:** Task Group 1

- [x] 2.0 Complete documentation structure
  - [x] 2.1 Write 2-8 focused tests for documentation generation
    - Limit to 2-8 highly focused tests maximum
    - Test specifications landing page structure
    - Test Product section with MyST include directives
    - Test Features section with extracted metadata
    - Test relative path resolution from docs/ to agent-os/
    - Skip exhaustive testing of all MyST directive variations
  - [x] 2.2 Create specifications landing page
    - Create new file: `docs/specifications/index.md`
    - Follow MyST Markdown pattern from `docs/examples/index.md`
    - Include overview section explaining specifications content
    - Use `{toctree}` directive with maxdepth: 2 and hidden option
    - Set proper heading structure (H1, H2) matching existing docs
  - [x] 2.3 Create Product section
    - Add "Product" H2 heading with descriptive introductory text
    - Create three subsections (H3): Mission, Roadmap, Tech Stack
    - For each subsection:
      - Include descriptive heading
      - Display extracted summary text (2-3 sentences)
      - Add "Read More" markdown link to full document
    - Use relative paths from `docs/specifications/` to `agent-os/product/`
    - Use `{include}` directive to embed full product documents
    - Set `:relative-docs:` option for proper link handling
  - [x] 2.4 Create Features section
    - Add "Features" H2 heading with descriptive text about development evolution
    - Create subsection (H3) for each spec in chronological order
    - For each spec subsection:
      - Use extracted title as heading
      - Display extracted summary (1-2 sentences)
      - Add "Read More" markdown link to full spec
    - Use relative paths from `docs/specifications/` to `agent-os/specs/*/spec.md`
    - Use `{include}` directive to embed full spec documents
    - Set `:relative-docs:` option for proper link handling
  - [x] 2.5 Add hidden toctree
    - Add `{toctree}` directive at bottom of page
    - Set `:maxdepth: 2` and `:hidden:` options
    - List all product documents in order
    - List all spec documents in chronological order
    - Follow pattern from `docs/examples/index.md`
  - [x] 2.6 Ensure documentation structure tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify correct MyST Markdown syntax
    - Verify proper include directive usage
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- `docs/specifications/index.md` created with proper structure
- Product section includes all three files with summaries
- Features section includes all specs in chronological order
- MyST directives are correctly formatted
- Relative paths resolve correctly
- Hidden toctree includes all documents

### Navigation Integration

#### Task Group 3: Main Documentation Navigation
**Dependencies:** Task Group 2

- [x] 3.0 Complete navigation integration
  - [x] 3.1 Write 2-8 focused tests for navigation integration
    - Limit to 2-8 highly focused tests maximum
    - Test specifications entry in main toctree
    - Test navigation hierarchy and breadcrumbs
    - Test Sphinx build success with new section
    - Skip exhaustive testing of all navigation scenarios
  - [x] 3.2 Update main documentation index
    - Edit `docs/index.md` to add specifications section
    - Insert "specifications/index" in toctree after "api-reference"
    - Maintain existing toctree options (maxdepth: 2, hidden)
    - Ensure proper indentation and formatting
  - [x] 3.3 Update "Next Steps" section
    - Add mention of Specifications section in `docs/index.md`
    - Include brief description of what readers will find
    - Maintain consistent styling with existing navigation links
    - Place after API Reference mention
  - [x] 3.4 Verify navigation hierarchy
    - Ensure Specifications appears in main navigation
    - Verify breadcrumb trail displays correctly
    - Check that subsections are accessible from main index
    - Test navigation flow from main page to specifications
  - [x] 3.5 Ensure navigation integration tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify navigation structure is correct
    - Verify Sphinx build completes successfully
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- Specifications entry added to main toctree
- Navigation appears correctly in published docs
- Breadcrumbs display proper hierarchy
- Next Steps section updated
- Sphinx build succeeds without errors

### Claude Skill & Documentation

#### Task Group 4: Skill Generation and Build Verification
**Dependencies:** Task Group 3

- [x] 4.0 Complete skill generation and final verification
  - [x] 4.1 Write 2-8 focused tests for build verification
    - Limit to 2-8 highly focused tests maximum
    - Test full Sphinx build with specifications section
    - Test generated HTML structure and links
    - Test relative path resolution in built documentation
    - Skip exhaustive testing of all documentation scenarios
  - [x] 4.2 Generate Claude Skill file
    - Create `specs-into-sphinx.md` skill file
    - Document the discovery logic for finding spec directories
    - Document extraction patterns for titles and summaries
    - Document MyST directive usage for includes and toctrees
    - Include guidance on relative path handling from docs/ to agent-os/
    - Provide reusable template for similar documentation integration
    - Store in `.claude/skills/` directory following project conventions
  - [x] 4.3 Run full Sphinx build
    - Execute `sphinx-build` command to build complete documentation
    - Verify build completes without errors or warnings
    - Check that specifications section appears in output
    - Verify all links resolve correctly
  - [x] 4.4 Verify generated documentation
    - Open built HTML in browser
    - Navigate to Specifications section from main page
    - Click through to Product subsections
    - Click through to Features subsections
    - Verify all "Read More" links work correctly
    - Check that embedded content displays properly
  - [x] 4.5 Test relative path resolution
    - Verify images load correctly if present in specs
    - Verify internal links within specs resolve correctly
    - Verify cross-references work between documents
    - Test navigation between different specification pages
  - [x] 4.6 Ensure build verification tests pass
    - Run ONLY the 2-8 tests written in 4.1
    - Verify complete build succeeds
    - Verify generated HTML is correct
    - Do NOT run unrelated test suites at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 4.1 pass
- Claude Skill file created with comprehensive guidance
- Full Sphinx build completes successfully
- All specifications appear in generated documentation
- Navigation works correctly in browser
- All links and embedded content display properly
- No build errors or warnings

## Execution Order

Recommended implementation sequence:
1. Discovery & Metadata Extraction (Task Group 1)
2. Documentation Structure (Task Group 2)
3. Navigation Integration (Task Group 3)
4. Claude Skill & Documentation (Task Group 4)

## Notes

**Testing Approach:**
- This feature is documentation-focused rather than code-focused
- Tests should verify file discovery, metadata extraction, and build success
- Each task group writes 2-8 focused tests before implementation
- Final verification in Task Group 4 ensures end-to-end functionality

**MyST Markdown Patterns:**
- Follow existing patterns from `docs/index.md` and `docs/examples/index.md`
- Use `{include}` directive with `:relative-docs:` option
- Use `{toctree}` directive with `:maxdepth:` and `:hidden:` options
- Maintain consistent heading structure (H1, H2, H3)

**Path Handling:**
- All file operations use absolute paths (cwd resets between bash calls)
- Documentation uses relative paths from `docs/` directory
- Include directives reference `../../agent-os/` for product and specs
- Verify path resolution in built HTML documentation

**Exclusions:**
- Exclude current spec directory (`2025-12-27-specifications-into-sphinx`)
- Include all other spec directories with date prefix pattern
- No filtering or categorization beyond chronological ordering

**Content Extraction Guidelines:**
- Product summaries: 2-3 sentences from intro paragraphs
- Spec titles: Remove "Specification: " prefix for cleaner display
- Spec summaries: 1-2 sentences from Goal section
- Handle missing sections gracefully with fallback to first paragraph
