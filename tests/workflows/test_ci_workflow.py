"""Tests for CI workflow configuration.

These tests verify the structure and behavior of the GitHub Actions CI workflow.
They focus on critical configuration aspects without testing GitHub Actions internals.
"""

from pathlib import Path

import yaml


def test_ci_workflow_exists():
    """Verify that the CI workflow file exists."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    )
    assert workflow_path.exists(), "CI workflow file should exist"


def test_ci_workflow_valid_yaml():
    """Verify that the CI workflow is valid YAML."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)
    assert config is not None, "CI workflow should be valid YAML"
    assert isinstance(config, dict), "CI workflow should be a dictionary"


def test_ci_workflow_triggers():
    """Verify that the CI workflow triggers on push and pull_request."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)

    # In YAML, "on" is a reserved word and gets parsed as True (boolean)
    # The actual triggers are stored under the True key
    triggers = config.get(True, config.get("on", []))
    assert isinstance(triggers, list), "CI workflow triggers should be a list"
    assert "push" in triggers, "CI workflow should trigger on push"
    assert "pull_request" in triggers, "CI workflow should trigger on pull_request"


def test_ci_workflow_uses_setup_just_action():
    """Verify that the CI workflow uses extractions/setup-just@v2 action."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)

    jobs = config.get("jobs", {})
    ci_tests_job = jobs.get("ci_tests", {})
    steps = ci_tests_job.get("steps", [])

    # Find the install just step
    install_just_step = None
    for step in steps:
        if "just" in step.get("name", "").lower():
            install_just_step = step
            break

    assert install_just_step is not None, (
        "CI workflow should have a step for installing just"
    )
    assert "uses" in install_just_step, "Install just step should use an action"
    assert "extractions/setup-just@v2" in install_just_step["uses"], (
        "CI workflow should use extractions/setup-just@v2 action"
    )


def test_ci_workflow_runs_ci_checks_ft():
    """Verify that the CI workflow runs 'just ci-checks-ft' command."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)

    jobs = config.get("jobs", {})
    ci_tests_job = jobs.get("ci_tests", {})
    steps = ci_tests_job.get("steps", [])

    # Find the CI checks step
    ci_checks_step = None
    for step in steps:
        if "run" in step and "ci-checks-ft" in step["run"]:
            ci_checks_step = step
            break

    assert ci_checks_step is not None, "CI workflow should run 'just ci-checks-ft'"


def test_ci_workflow_has_coverage_threshold_check():
    """Verify that the CI workflow has a coverage threshold reporting step."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)

    jobs = config.get("jobs", {})
    ci_tests_job = jobs.get("ci_tests", {})
    steps = ci_tests_job.get("steps", [])

    # Find the coverage threshold check step
    coverage_step = None
    for step in steps:
        if (
            "coverage" in step.get("name", "").lower()
            and "threshold" in step.get("name", "").lower()
        ):
            coverage_step = step
            break

    assert coverage_step is not None, (
        "CI workflow should have a coverage threshold check step"
    )
    assert "run" in coverage_step, "Coverage threshold step should have a run command"
    # Verify it uses the Justfile recipe that checks threshold
    assert "just coverage-report" in coverage_step["run"], (
        "Coverage threshold should use 'just coverage-report' recipe"
    )


def test_ci_workflow_timeout():
    """Verify that the CI workflow has a 30-minute timeout."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)

    jobs = config.get("jobs", {})
    ci_tests_job = jobs.get("ci_tests", {})
    timeout = ci_tests_job.get("timeout-minutes")

    assert timeout == 30, "CI workflow should have a 30-minute timeout"
