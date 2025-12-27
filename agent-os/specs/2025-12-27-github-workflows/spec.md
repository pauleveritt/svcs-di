# Specification: GitHub Workflows for CI/CD

## Goal

Implement comprehensive GitHub Actions workflows for continuous integration testing with Python 3.14.2t (free-threaded),
documentation deployment to GitHub Pages, and reusable composite actions for dependency management using uv.

## User Stories

- As a developer, I want automated CI testing with free-threaded Python 3.14.2t so that I can ensure code quality and
  thread safety before merging changes
- As a documentation maintainer, I want automatic documentation deployment to GitHub Pages so that users always have
  access to the latest documentation

## Specific Requirements

**Main CI Workflow**

- Update `.github/workflows/ci.yml` to test only Python 3.14.2t (free-threaded build)
- Trigger on all push and pull request events
- Run `just ci-checks-ft` which includes quality checks, coverage testing, and free-threaded safety tests
- Use composite action for setup steps to ensure consistency
- Install just using `extractions/setup-just@v2` action instead of curl
- Set 30-minute timeout for CI jobs
- Report coverage with warning if below 80% threshold (non-blocking)

**Documentation Deployment Workflow**

- Create new `.github/workflows/pages.yml` for GitHub Pages deployment
- Trigger on push to main branch and manual workflow_dispatch
- Include separate build and deploy jobs with proper dependency chain
- Build job runs `just docs-build` to generate Sphinx documentation
- Upload built documentation as artifact to GitHub Pages
- Deploy job deploys the artifact to GitHub Pages environment
- Set appropriate permissions (contents: read, pages: write, id-token: write)
- Use concurrency controls (group: "pages", cancel-in-progress: false) to prevent deployment conflicts

**Composite Action for Python/uv Setup**

- Composite action already exists at `.github/actions/setup-python-uv/action.yml`
- Restores .venv cache based on uv.lock hash for faster builds
- Installs uv using `astral-sh/setup-uv@v7` with caching enabled
- Sets up Python 3.14.2t by running `uv python install` (reads from .python-version file)
- Installs dependencies using `uv sync --frozen` for reproducible builds
- Both CI and Pages workflows should reuse this composite action

**Justfile Integration**

- CI workflow executes `just ci-checks-ft` command which includes quality checks, test-cov, and test-run-parallel
- Quality checks include Ruff linting, Ruff format-check, and ty type checking with PYTHONPATH=examples
- Coverage tests run with pytest-cov generating term-missing and HTML reports
- Free-threaded safety tests run with pytest-run-parallel using 8 parallel threads and 10 iterations
- Documentation workflow executes `just docs-build` command using sphinx-build with -W flag

**Coverage Reporting**

- Coverage runs as part of `test-cov` recipe in ci-checks-ft
- Generate both terminal output (term-missing) and HTML reports
- Check coverage threshold of 80% in workflow output
- Report coverage below 80% as warning message (do not fail the build)
- No integration with external services like Codecov or Coveralls

**Dependency Caching**

- Use uv.lock file hash for cache key to ensure proper cache invalidation
- Cache .venv directory to speed up dependency installation
- Composite action handles all caching logic with actions/cache@v4
- setup-uv action includes its own caching with cache-dependency-glob: "uv.lock"

**GitHub Actions Versions**

- actions/checkout@v4 for repository checkout
- astral-sh/setup-uv@v7 for uv installation with caching
- extractions/setup-just@v2 for just installation
- actions/cache@v4 for .venv caching in composite action
- actions/upload-pages-artifact@v3 for documentation artifact upload
- actions/deploy-pages@v4 for GitHub Pages deployment

**Workflow Permissions and Concurrency**

- CI workflow uses default permissions
- Pages workflow requires elevated permissions for GitHub Pages deployment
- Pages workflow uses concurrency group "pages" to prevent conflicting deployments
- Set cancel-in-progress: false to allow production deployments to complete

## Visual Design

No visual assets provided.

## Existing Code to Leverage

**Reference Project: tdom-path**

- CI workflow structure at `/Users/pauleveritt/projects/t-strings/tdom-path/.github/workflows/ci.yml` provides model for
  job structure, timeout settings, and step organization
- Pages workflow at `/Users/pauleveritt/projects/t-strings/tdom-path/.github/workflows/pages.yml` shows complete GitHub
  Pages deployment pattern with build/deploy jobs, permissions, and concurrency controls
- Composite action at `/Users/pauleveritt/projects/t-strings/tdom-path/.github/actions/setup-python-uv/action.yml`
  demonstrates cache restoration, uv installation, Python setup, and dependency installation pattern
- Reference project uses extractions/setup-just@v2 in pages workflow while current project uses curl installation
- Reference project runs `just docs` command while current project should run `just docs-build`

**Current Project: svcs-di**

- Existing composite action at `.github/actions/setup-python-uv/action.yml` already implements the required setup steps
  and matches reference project pattern
- Current `.github/workflows/ci.yml` has correct structure but needs just installation method updated from curl to
  extractions/setup-just@v2
- Justfile at project root has `ci-checks-ft` recipe (line 91) that runs quality, test-cov, and test-run-parallel
  sequentially
- Justfile has `docs-build` recipe (line 58) that runs sphinx-build with correct flags
- .python-version file contains `3.14.2t` which specifies free-threaded Python 3.14.2

**pytest-run-parallel Configuration**

- pyproject.toml already includes pytest-run-parallel in dev dependencies (line 29)
- pytest configuration includes freethreaded marker (line 46) for test categorization
- Justfile test-run-parallel recipe (line 87) runs pytest with --parallel-threads=8 and --iterations=10
- Timeout settings configured in pyproject.toml (lines 49-50) for hang/deadlock detection

**Coverage Configuration**

- pyproject.toml includes pytest-cov and coverage packages in dev dependencies (lines 21, 27)
- Justfile test-cov recipe (line 16) runs pytest with --cov=svcs_di, --cov-report=term-missing, and --cov-report=html
- Coverage report outputs to terminal and htmlcov/ directory

## Out of Scope

- Testing multiple Python versions (3.12, 3.13, regular 3.14) - only 3.14.2t free-threaded
- External coverage service integration (Codecov, Coveralls)
- Automated PyPI publishing on release tags
- Dependabot configuration for dependency updates
- Stale issue or pull request management workflows
- Automated changelog generation
- Security scanning workflows (CodeQL, Snyk, etc.)
- Matrix testing with both regular and free-threaded Python 3.14
- Separate jobs for linting, type checking, and testing - all run together in ci-checks-ft
- Coverage failure threshold enforcement - coverage below 80% only warns, does not fail build
