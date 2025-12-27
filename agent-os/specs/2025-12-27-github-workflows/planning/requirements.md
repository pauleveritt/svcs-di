# Spec Requirements: GitHub Workflows

## Initial Description
11 - GitHub Workflows

Based on roadmap item 11: "Analyze `~/projects/t-strings/tdom-path/` for a project with the correct structure. Look in its `.github` for the setup, `Justfile` for the recipes, and any `pyproject.toml` for any dependencies."

## Requirements Discussion

### First Round Questions

**Q1:** I assume you want to set up CI/CD workflows similar to the reference project at `~/projects/t-strings/tdom-path/`, running tests across multiple Python versions including free-threaded builds, plus linting with Ruff and coverage reporting. Is that correct, or do you have different requirements?
**Answer:** Yes but only threaded/not-threaded for Python 3.14

**Q2:** I'm thinking the workflows should run on every push and pull request to the main branch, with separate jobs for: (a) linting/formatting checks with Ruff, (b) type checking, (c) test suite across Python 3.12, 3.13, 3.14, and 3.14t (free-threaded), and (d) documentation builds. Should we include all of these, or prioritize differently?
**Answer:** Yes (include all jobs: linting/formatting with Ruff, type checking, test suite across Python versions, and documentation builds)

**Q3:** For the free-threaded Python testing (3.14t), I assume we should use pytest-freethreaded as mentioned in your tech stack and run it as a separate job to verify PEP 703 compatibility. Should this be a required check or optional/informational?
**Answer:** No use `pytest-run-parallel` (not pytest-freethreaded)

**Q4:** I'm thinking we should integrate the existing `Justfile` commands into the GitHub Actions workflows, so the CI uses the same commands developers use locally (like `just test`, `just lint`, etc.). This would ensure consistency between local and CI environments. Does that align with your approach?
**Answer:** Yes (integrate Justfile commands into GitHub Actions workflows)

**Q5:** Looking at the roadmap, item 11 specifically mentions analyzing dependencies in `pyproject.toml` from the reference project. Should the workflows handle dependency caching with uv, and are there any specific dependency groups (like dev, test, docs) that should be installed conditionally per job?
**Answer:** Yes for caching, no for specific dependency groups

**Q6:** For coverage reporting, should we upload coverage results to a service like Codecov or Coveralls, or just report coverage in the workflow output? Also, what's your target coverage threshold (if any)?
**Answer:** No external coverage service and 80% coverage threshold

**Q7:** Should the workflows include automated publishing to PyPI on tagged releases, or is that out of scope for this initial setup?
**Answer:** No automated PyPI publishing

**Q8:** Are there any workflows you specifically DON'T want? For example: dependency updates via Dependabot, stale issue management, automated changelog generation, or security scanning?
**Answer:** No to Dependabot, stale issue management, automated changelog generation, or security scanning

### Existing Code to Reference

**Similar Features Identified:**
- Reference project: `/Users/pauleveritt/projects/t-strings/tdom-path/`
  - `.github/workflows/ci.yml` - Main CI workflow structure
  - `.github/workflows/pages.yml` - Documentation deployment workflow
  - `.github/actions/setup-python-uv/action.yml` - Reusable composite action
  - `Justfile` - Reference for CI commands
- Current project already has:
  - `.github/workflows/ci.yml` - Existing minimal CI (only 3.14t)
  - `.github/actions/` - Directory needs setup-python-uv composite action
  - `Justfile` - With `ci-checks` and `ci-checks-ft` recipes
  - `pyproject.toml` - With pytest-run-parallel configured

### Follow-up Questions

**Follow-up 1:** I notice your current `.github/workflows/ci.yml` only tests Python 3.14t (free-threaded). You mentioned wanting both threaded and non-threaded for Python 3.14. Should the new workflow have TWO separate jobs: one for Python 3.14 (regular) and one for Python 3.14t (free-threaded), or should we create a matrix that tests both?
**Answer:** No just use 3.14.2t (only free-threaded Python 3.14, not both regular and free-threaded)

**Follow-up 2:** The reference project uses a custom composite action (`.github/actions/setup-python-uv/action.yml`) for reusable setup steps. Should we create the same reusable action for your svcs-di project, or inline all the setup steps in each workflow job?
**Answer:** Reuse composite (create a custom composite action like the reference project)

**Follow-up 3:** For the documentation build workflow, I see the reference project has a separate `pages.yml` that builds and deploys to GitHub Pages on push to main. Do you want: (a) just a docs build job in the main CI workflow that verifies docs build successfully, or (b) a separate workflow that builds AND deploys docs to GitHub Pages?
**Answer:** Do the same as `tdom-path` (separate workflow that builds AND deploys docs to GitHub Pages)

**Follow-up 4:** Your Justfile has `ci-checks` (quality + test-cov) and `ci-checks-ft` (adds free-threaded tests). For the regular Python 3.14 job, should it run `just ci-checks`, and the 3.14t job run `just ci-checks-ft`?
**Answer:** Yes (run `just ci-checks` for regular jobs and `just ci-checks-ft` for free-threaded job)

**Follow-up 5:** The reference project uses `extractions/setup-just@v2` action for installing just, but your current ci.yml uses a curl command. Which approach should the new workflows use?
**Answer:** `setup-just@v2` (use the extractions/setup-just@v2 action)

**Follow-up 6:** For the 80% coverage threshold you mentioned, should the workflow FAIL if coverage drops below 80%, or just report it as a warning? And should this threshold be enforced in the pytest configuration or checked as a separate step in the workflow?
**Answer:** Report with warning (don't fail the workflow, just report if coverage drops below 80%)

## Visual Assets

### Files Provided:
No visual assets provided.

### Visual Insights:
Not applicable - infrastructure configuration does not require visual mockups.

## Requirements Summary

### Functional Requirements

**Main CI Workflow (`ci.yml`):**
- Trigger on all pushes and pull requests
- Single job testing Python 3.14.2t (free-threaded build only)
- Run `just ci-checks-ft` which includes:
  - Quality checks (linting with Ruff, formatting checks, type checking with ty)
  - Test suite with coverage reporting
  - Free-threaded safety tests using pytest-run-parallel
- Report coverage with warning if below 80% threshold (non-blocking)
- Use composite action for setup steps
- Install just using `extractions/setup-just@v2` action
- Use uv for dependency caching

**Documentation Deployment Workflow (`pages.yml`):**
- Separate workflow that builds AND deploys documentation to GitHub Pages
- Trigger on push to main branch and manual workflow_dispatch
- Build job:
  - Use composite action for setup
  - Install just using `extractions/setup-just@v2`
  - Run `just docs-build` to build Sphinx documentation
  - Upload artifact to GitHub Pages
- Deploy job:
  - Deploy built documentation to GitHub Pages
  - Set appropriate permissions for GitHub Pages deployment
  - Use concurrency controls to prevent deployment conflicts

**Composite Action (`setup-python-uv/action.yml`):**
- Reusable setup steps for both CI and docs workflows
- Restore .venv cache based on uv.lock hash
- Install uv using `astral-sh/setup-uv@v7` with caching enabled
- Set up Python 3.14t using `uv python install` (reads from .python-version)
- Install dependencies using `uv sync --frozen`

**Justfile Integration:**
- CI workflow uses `just ci-checks-ft` command
- Docs workflow uses `just docs-build` command
- Ensures consistency between local development and CI environments

**Coverage Reporting:**
- No external service (Codecov/Coveralls)
- Report coverage in workflow output
- 80% coverage threshold as warning (non-blocking)
- Coverage HTML report generated but not uploaded

### Reusability Opportunities

**Reference Project Patterns:**
- Copy structure from `/Users/pauleveritt/projects/t-strings/tdom-path/.github/`
- Reuse composite action pattern for setup-python-uv
- Model ci.yml structure on reference project's approach
- Model pages.yml deployment workflow on reference project

**Existing Project Elements:**
- Current `.github/workflows/ci.yml` will be replaced/updated
- Existing `Justfile` recipes (`ci-checks-ft`, `docs-build`) are already prepared
- `pyproject.toml` already has pytest-run-parallel configured
- `.python-version` file should specify `3.14t` for free-threaded build

### Scope Boundaries

**In Scope:**
- Main CI workflow testing Python 3.14.2t (free-threaded)
- Composite action for Python/uv setup with caching
- Documentation build and deployment workflow to GitHub Pages
- Integration with existing Justfile recipes
- Coverage reporting with 80% warning threshold
- uv dependency caching for faster builds

**Out of Scope:**
- Multiple Python version testing (3.12, 3.13, 3.14 regular)
- External coverage service integration (Codecov/Coveralls)
- Automated PyPI publishing on release tags
- Dependabot for dependency updates
- Stale issue/PR management
- Automated changelog generation
- Security scanning workflows
- Regular (non-free-threaded) Python 3.14 testing

### Technical Considerations

**Python Version:**
- Only Python 3.14.2t (free-threaded build)
- Specified via .python-version file: `3.14t`
- Installed via `uv python install`

**Dependency Management:**
- Use uv for all dependency operations
- Cache .venv based on uv.lock hash
- Use `uv sync --frozen` for reproducible installs
- No conditional dependency groups (install all dev dependencies)

**Testing Framework:**
- pytest with pytest-run-parallel (NOT pytest-freethreaded)
- Free-threading tests via `pytest -p no:doctest --parallel-threads=8 --iterations=10`
- Coverage via pytest-cov with HTML reports
- Tests run via `just ci-checks-ft`

**Quality Checks:**
- Ruff for linting and formatting checks
- ty for type checking with PYTHONPATH=examples
- All checks run via `just quality` (part of ci-checks-ft)

**Documentation:**
- Sphinx for documentation generation
- Build via `just docs-build`
- Deploy to GitHub Pages on main branch pushes
- Separate workflow from CI tests

**GitHub Actions Versions:**
- actions/checkout@v4
- astral-sh/setup-uv@v7
- extractions/setup-just@v2
- actions/cache@v4 (via composite action)
- actions/upload-pages-artifact@v3 (for docs)
- actions/deploy-pages@v4 (for docs)

**Workflow Configuration:**
- Timeout: 30 minutes for CI jobs, 10 minutes for deploy
- Trigger: push and pull_request for CI, push to main for docs
- Permissions: Standard for CI, elevated for GitHub Pages deployment
- Concurrency: Pages deployment uses concurrency group to prevent conflicts

**Coverage Threshold:**
- 80% minimum coverage
- Reported as warning if below threshold
- Does not fail the workflow
- Implementation: check coverage report output in CI step
