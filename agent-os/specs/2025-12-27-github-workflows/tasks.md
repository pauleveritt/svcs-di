# Task Breakdown: GitHub Workflows for CI/CD

## Overview
Total Tasks: 13 across 3 task groups

This feature implements GitHub Actions workflows for continuous integration testing with Python 3.14.2t (free-threaded) and automated documentation deployment to GitHub Pages. The implementation leverages existing composite actions, Justfile recipes, and follows patterns from the reference project at `/Users/pauleveritt/projects/t-strings/tdom-path/`.

## Task List

### Workflow Configuration Layer

#### Task Group 1: CI Workflow Update
**Dependencies:** None

- [x] 1.0 Update CI workflow for free-threaded Python testing
  - [x] 1.1 Write 2-8 focused tests to verify CI workflow behavior
    - Limit to 2-8 highly focused tests maximum
    - Test only critical workflow scenarios (e.g., workflow triggers correctly, composite action is invoked, just commands execute)
    - Skip exhaustive testing of all possible CI scenarios
    - Note: These are integration tests that verify the workflow file structure and key execution paths
  - [x] 1.2 Update `.github/workflows/ci.yml` just installation method
    - Replace curl installation (lines 18-19) with `extractions/setup-just@v2` action
    - Reference pattern from: `/Users/pauleveritt/projects/t-strings/tdom-path/.github/workflows/pages.yml` (line 34)
    - Maintain existing workflow structure (trigger, timeout, steps)
  - [x] 1.3 Add coverage threshold reporting step
    - Add new step after `just ci-checks-ft` execution
    - Parse coverage output and check for 80% threshold
    - Report warning message if coverage below 80% (non-blocking)
    - Use `continue-on-error: false` to ensure step runs but doesn't fail workflow
  - [x] 1.4 Verify workflow file syntax and structure
    - Ensure YAML syntax is valid
    - Verify all action versions are correct (checkout@v4, setup-just@v2)
    - Confirm composite action reference path is correct
  - [x] 1.5 Ensure CI workflow tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify workflow file validates successfully
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- CI workflow uses `extractions/setup-just@v2` instead of curl
- Coverage reporting shows warning for sub-80% coverage without failing build
- Workflow triggers on push and pull_request events
- 30-minute timeout is maintained
- Composite action is properly referenced

**Files Modified:**
- `/Users/pauleveritt/projects/pauleveritt/svcs-di/.github/workflows/ci.yml`

**Reference Files:**
- `/Users/pauleveritt/projects/t-strings/tdom-path/.github/workflows/pages.yml` (lines 33-34 for setup-just usage)
- `/Users/pauleveritt/projects/pauleveritt/svcs-di/justfile` (line 91 for ci-checks-ft recipe)

---

#### Task Group 2: Documentation Deployment Workflow
**Dependencies:** Task Group 1 (composite action must exist)

- [x] 2.0 Create documentation deployment workflow
  - [x] 2.1 Write 2-8 focused tests for Pages workflow
    - Limit to 2-8 highly focused tests maximum
    - Test only critical deployment scenarios (e.g., workflow triggers on main branch, build job executes, deploy job depends on build)
    - Skip exhaustive testing of all deployment edge cases
    - Note: These are integration tests that verify workflow structure and deployment configuration
  - [x] 2.2 Create `.github/workflows/pages.yml` for GitHub Pages
    - Use structure from: `/Users/pauleveritt/projects/t-strings/tdom-path/.github/workflows/pages.yml`
    - Set workflow name to "Deploy documentation to Pages"
    - Configure triggers: push to main branch and workflow_dispatch
  - [x] 2.3 Configure permissions and concurrency controls
    - Set permissions: `contents: read`, `pages: write`, `id-token: write`
    - Add concurrency group: `"pages"` with `cancel-in-progress: false`
    - Reference: reference project lines 11-20
  - [x] 2.4 Implement build job
    - Name: "Build svcs-di documentation site"
    - Run on: ubuntu-latest with 30-minute timeout
    - Steps: checkout, setup Python/uv (composite action), install just, build docs
    - Execute: `just docs-build` (not `just docs` like reference project)
    - Upload artifact using `actions/upload-pages-artifact@v3` with path `./docs/_build/html`
  - [x] 2.5 Implement deploy job
    - Name: "deploy"
    - Depends on: build job (needs: build)
    - Environment: github-pages with output URL
    - Run on: ubuntu-latest with 10-minute timeout
    - Deploy using `actions/deploy-pages@v4`
  - [x] 2.6 Ensure Pages workflow tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify workflow file structure is valid
    - Confirm build and deploy jobs are properly configured
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- Pages workflow triggers on push to main and manual dispatch
- Build job uses composite action and runs `just docs-build`
- Deploy job depends on successful build
- Proper permissions for GitHub Pages deployment
- Concurrency controls prevent conflicting deployments
- Workflow files validate successfully

**Files Created:**
- `/Users/pauleveritt/projects/pauleveritt/svcs-di/.github/workflows/pages.yml`

**Reference Files:**
- `/Users/pauleveritt/projects/t-strings/tdom-path/.github/workflows/pages.yml` (complete structure)
- `/Users/pauleveritt/projects/pauleveritt/svcs-di/justfile` (line 58 for docs-build recipe)

---

### Testing and Validation Layer

#### Task Group 3: Workflow Integration Testing
**Dependencies:** Task Groups 1-2 (all workflows must be implemented)

- [x] 3.0 Test workflow integration and validate deployment
  - [x] 3.1 Review tests from Task Groups 1-2
    - Review the 2-8 tests written for CI workflow (Task 1.1)
    - Review the 2-8 tests written for Pages workflow (Task 2.1)
    - Total existing tests: approximately 4-16 tests
  - [x] 3.2 Analyze workflow integration gaps
    - Identify missing test coverage for workflow interactions
    - Focus ONLY on gaps related to CI and Pages workflow integration
    - Do NOT assess entire GitHub Actions configuration
    - Prioritize end-to-end workflow execution over configuration details
  - [x] 3.3 Write up to 10 additional integration tests maximum
    - Add maximum of 10 new tests to fill critical gaps
    - Focus on workflow triggers, job dependencies, and artifact handling
    - Test composite action reusability across both workflows
    - Verify coverage reporting logic in CI workflow
    - Test documentation build and artifact upload process
    - Do NOT write comprehensive tests for all GitHub Actions features
  - [x] 3.4 Run local workflow validation
    - Validate both workflow YAML files for syntax errors
    - Check action versions are compatible and up-to-date
    - Verify composite action is correctly referenced from both workflows
  - [x] 3.5 Test CI workflow locally (if possible)
    - Run `just ci-checks-ft` to verify it works as expected
    - Confirm coverage reports are generated correctly
    - Verify all quality checks, tests, and free-threading tests pass
  - [x] 3.6 Test documentation build locally
    - Run `just docs-build` to verify documentation builds successfully
    - Confirm Sphinx generates HTML output in `docs/_build/html`
    - Check for any build warnings or errors (Sphinx uses -W flag)
  - [x] 3.7 Verify GitHub Actions configuration
    - Check that repository has GitHub Pages enabled (if not, document requirement)
    - Verify workflow files are in correct location (`.github/workflows/`)
    - Confirm composite action is in correct location (`.github/actions/setup-python-uv/`)
  - [x] 3.8 Run workflow-specific tests
    - Run ONLY tests related to workflow functionality (tests from 1.1, 2.1, and 3.3)
    - Expected total: approximately 14-42 tests maximum
    - Do NOT run the entire application test suite
    - Verify workflow configuration and structure is correct

**Acceptance Criteria:**
- All workflow-specific tests pass (approximately 14-42 tests total)
- No more than 10 additional tests added when filling integration gaps
- Both workflow YAML files are syntactically valid
- CI workflow successfully runs `just ci-checks-ft` with coverage reporting
- Pages workflow successfully builds and deploys documentation
- Composite action works correctly in both workflows
- All GitHub Actions use specified versions (checkout@v4, setup-uv@v7, setup-just@v2, cache@v4, upload-pages-artifact@v3, deploy-pages@v4)
- Coverage threshold warning appears when coverage drops below 80%
- Testing focused exclusively on workflow functionality

**Files Validated:**
- `/Users/pauleveritt/projects/pauleveritt/svcs-di/.github/workflows/ci.yml`
- `/Users/pauleveritt/projects/pauleveritt/svcs-di/.github/workflows/pages.yml`
- `/Users/pauleveritt/projects/pauleveritt/svcs-di/.github/actions/setup-python-uv/action.yml`

**Manual Verification Required:**
- Push to repository to trigger CI workflow
- Merge to main branch to trigger Pages deployment
- Verify GitHub Pages deployment succeeds
- Check coverage reporting appears in CI logs
- Confirm documentation is accessible at GitHub Pages URL

---

## Execution Order

Recommended implementation sequence:
1. **Workflow Configuration Layer** (Task Groups 1-2): Implement both workflow files
   - Task Group 1: Update CI workflow with proper just installation and coverage reporting
   - Task Group 2: Create Pages workflow for documentation deployment
2. **Testing and Validation Layer** (Task Group 3): Comprehensive integration testing and validation

## Implementation Notes

### Key Differences from Reference Project

1. **Justfile Command**: Current project uses `just docs-build` (not `just docs`)
2. **Just Installation**: CI workflow currently uses curl, needs update to `extractions/setup-just@v2`
3. **Python Version**: Only testing Python 3.14.2t (free-threaded), no matrix of versions
4. **Coverage Reporting**: Added coverage threshold check as workflow step (not in reference project)

### Existing Assets to Leverage

1. **Composite Action**: Already exists at `.github/actions/setup-python-uv/action.yml`
   - Handles cache restoration with uv.lock hash
   - Installs uv with caching enabled
   - Sets up Python 3.14t from .python-version
   - Installs dependencies with `uv sync --frozen`
   - No modifications needed, reuse as-is

2. **Justfile Recipes**: Already configured and ready
   - `ci-checks-ft` (line 91): Runs quality, test-cov, test-run-parallel
   - `docs-build` (line 58): Runs sphinx-build with -W flag
   - No changes needed to Justfile

3. **Python Configuration**:
   - `.python-version` contains `3.14.2t` for free-threaded Python
   - `pyproject.toml` has pytest-run-parallel configured (line 29)
   - Coverage configuration already set in pyproject.toml

### Testing Strategy

- **Minimal Test Coverage**: Each task group writes 2-8 focused tests maximum
- **Test Scope**: Focus on workflow configuration, structure, and critical execution paths
- **No Exhaustive Testing**: Skip edge cases, GitHub Actions API details, deployment infrastructure
- **Integration Focus**: Task Group 3 adds up to 10 tests for workflow interactions
- **Total Test Count**: Approximately 14-42 tests for entire workflow feature

### Coverage Reporting Implementation

The CI workflow needs a step to check coverage and report warnings:
```yaml
- name: Check coverage threshold
  run: |
    COVERAGE=$(uv run coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
    if (( $(echo "$COVERAGE < 80" | bc -l) )); then
      echo "::warning::Coverage is ${COVERAGE}% which is below the 80% threshold"
    else
      echo "Coverage is ${COVERAGE}% which meets the 80% threshold"
    fi
  continue-on-error: false
```

### GitHub Actions Versions Reference

- `actions/checkout@v4`: Repository checkout
- `astral-sh/setup-uv@v7`: uv installation with caching
- `extractions/setup-just@v2`: just installation (replaces curl method)
- `actions/cache@v4`: Dependency caching in composite action
- `actions/upload-pages-artifact@v3`: Upload docs artifact
- `actions/deploy-pages@v4`: Deploy to GitHub Pages

## Out of Scope

- Multiple Python version testing (only 3.14.2t free-threaded)
- External coverage service integration (Codecov, Coveralls)
- Automated PyPI publishing workflows
- Dependabot configuration
- Security scanning workflows
- Matrix testing strategies
- Separate jobs for linting, type checking, and testing (all run via just ci-checks-ft)
- Coverage failure enforcement (only warnings, not blocking)
