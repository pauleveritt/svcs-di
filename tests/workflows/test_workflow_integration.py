"""Integration tests for GitHub Actions workflows.

These tests verify that the CI and Pages workflows work together correctly,
focusing on workflow interactions and composite action reusability.
"""

from pathlib import Path

import yaml


def test_both_workflows_use_composite_action():
    """Verify that both CI and Pages workflows use the same composite action."""
    ci_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    pages_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )

    with open(ci_path) as f:
        ci_config = yaml.safe_load(f)
    with open(pages_path) as f:
        pages_config = yaml.safe_load(f)

    # Check CI workflow
    ci_steps = ci_config["jobs"]["ci_tests"]["steps"]
    ci_setup_step = next(
        (s for s in ci_steps if "setup" in s.get("name", "").lower()), None
    )
    assert ci_setup_step is not None, "CI workflow should have a setup step"
    assert ci_setup_step["uses"] == "./.github/actions/setup-python-uv", (
        "CI workflow should use setup-python-uv composite action"
    )

    # Check Pages workflow
    pages_steps = pages_config["jobs"]["build"]["steps"]
    pages_setup_step = next(
        (s for s in pages_steps if "setup" in s.get("name", "").lower()), None
    )
    assert pages_setup_step is not None, "Pages workflow should have a setup step"
    assert pages_setup_step["uses"] == "./.github/actions/setup-python-uv", (
        "Pages workflow should use setup-python-uv composite action"
    )


def test_both_workflows_use_setup_just_v2():
    """Verify that both workflows use extractions/setup-just@v2."""
    ci_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    pages_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )

    with open(ci_path) as f:
        ci_config = yaml.safe_load(f)
    with open(pages_path) as f:
        pages_config = yaml.safe_load(f)

    # Check CI workflow
    ci_steps = ci_config["jobs"]["ci_tests"]["steps"]
    ci_just_step = next(
        (s for s in ci_steps if "just" in s.get("name", "").lower()), None
    )
    assert ci_just_step is not None, "CI workflow should have a just installation step"
    assert "extractions/setup-just@v2" in ci_just_step["uses"], (
        "CI workflow should use extractions/setup-just@v2"
    )

    # Check Pages workflow
    pages_steps = pages_config["jobs"]["build"]["steps"]
    pages_just_step = next(
        (s for s in pages_steps if "just" in s.get("name", "").lower()), None
    )
    assert pages_just_step is not None, (
        "Pages workflow should have a just installation step"
    )
    assert "extractions/setup-just@v2" in pages_just_step["uses"], (
        "Pages workflow should use extractions/setup-just@v2"
    )


def test_composite_action_exists_and_valid():
    """Verify that the composite action file exists and is valid YAML."""
    action_path = (
        Path(__file__).parent.parent.parent
        / ".github"
        / "actions"
        / "setup-python-uv"
        / "action.yml"
    )
    assert action_path.exists(), "Composite action should exist"

    with open(action_path) as f:
        action_config = yaml.safe_load(f)

    assert action_config is not None, "Composite action should be valid YAML"
    assert action_config.get("runs", {}).get("using") == "composite", (
        "Action should be a composite action"
    )


def test_workflow_action_versions_consistency():
    """Verify that all workflows use consistent action versions."""
    ci_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    pages_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )

    with open(ci_path) as f:
        ci_config = yaml.safe_load(f)
    with open(pages_path) as f:
        pages_config = yaml.safe_load(f)

    # Check that both use actions/checkout@v4
    ci_checkout = next(
        (
            s
            for s in ci_config["jobs"]["ci_tests"]["steps"]
            if "checkout" in s.get("uses", "")
        ),
        None,
    )
    pages_checkout = next(
        (
            s
            for s in pages_config["jobs"]["build"]["steps"]
            if "checkout" in s.get("uses", "")
        ),
        None,
    )

    assert ci_checkout is not None, "CI workflow should have checkout step"
    assert pages_checkout is not None, "Pages workflow should have checkout step"
    assert ci_checkout["uses"] == "actions/checkout@v4", "CI should use checkout@v4"
    assert pages_checkout["uses"] == "actions/checkout@v4", (
        "Pages should use checkout@v4"
    )


def test_ci_workflow_coverage_reporting_non_blocking():
    """Verify that coverage reporting in CI workflow doesn't block on failure."""
    ci_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"

    with open(ci_path) as f:
        ci_config = yaml.safe_load(f)

    steps = ci_config["jobs"]["ci_tests"]["steps"]
    coverage_step = next(
        (
            s
            for s in steps
            if "coverage" in s.get("name", "").lower()
            and "threshold" in s.get("name", "").lower()
        ),
        None,
    )

    assert coverage_step is not None, "CI workflow should have coverage threshold step"
    # The step should not have continue-on-error: true, which means errors won't be ignored
    # But the script itself uses warning messages, not exit codes
    assert (
        coverage_step.get("continue-on-error") is False
        or "continue-on-error" not in coverage_step
    ), "Coverage step should not silently ignore errors"


def test_pages_workflow_build_before_deploy():
    """Verify that the Pages workflow builds before deploying."""
    pages_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )

    with open(pages_path) as f:
        pages_config = yaml.safe_load(f)

    jobs = pages_config["jobs"]
    assert "build" in jobs, "Pages workflow should have build job"
    assert "deploy" in jobs, "Pages workflow should have deploy job"

    deploy_job = jobs["deploy"]
    needs = deploy_job.get("needs")
    # needs can be a string or a list
    if isinstance(needs, str):
        assert needs == "build", "Deploy job should depend on build job"
    else:
        assert "build" in needs, "Deploy job should depend on build job"


def test_pages_workflow_artifact_upload_configuration():
    """Verify that the Pages workflow uploads the correct artifact."""
    pages_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )

    with open(pages_path) as f:
        pages_config = yaml.safe_load(f)

    build_steps = pages_config["jobs"]["build"]["steps"]
    upload_step = next(
        (
            s
            for s in build_steps
            if "upload" in s.get("uses", "") and "pages-artifact" in s.get("uses", "")
        ),
        None,
    )

    assert upload_step is not None, "Build job should upload pages artifact"
    assert upload_step.get("with", {}).get("path") == "./docs/_build/html", (
        "Artifact should be uploaded from ./docs/_build/html"
    )


def test_workflows_use_correct_justfile_commands():
    """Verify that workflows use the correct justfile commands."""
    ci_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    pages_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )

    with open(ci_path) as f:
        ci_config = yaml.safe_load(f)
    with open(pages_path) as f:
        pages_config = yaml.safe_load(f)

    # CI should run ci-checks-ft
    ci_steps = ci_config["jobs"]["ci_tests"]["steps"]
    ci_run_step = next(
        (s for s in ci_steps if s.get("run") == "just ci-checks-ft"), None
    )
    assert ci_run_step is not None, "CI workflow should run 'just ci-checks-ft'"

    # Pages should run docs-build
    pages_steps = pages_config["jobs"]["build"]["steps"]
    pages_run_step = next(
        (s for s in pages_steps if s.get("run") == "just docs-build"), None
    )
    assert pages_run_step is not None, "Pages workflow should run 'just docs-build'"


def test_workflows_have_appropriate_timeouts():
    """Verify that all workflow jobs have appropriate timeout settings."""
    ci_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
    pages_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )

    with open(ci_path) as f:
        ci_config = yaml.safe_load(f)
    with open(pages_path) as f:
        pages_config = yaml.safe_load(f)

    # CI tests should have 30-minute timeout
    assert ci_config["jobs"]["ci_tests"]["timeout-minutes"] == 30, (
        "CI job should have 30-minute timeout"
    )

    # Pages build should have 30-minute timeout
    assert pages_config["jobs"]["build"]["timeout-minutes"] == 30, (
        "Pages build job should have 30-minute timeout"
    )

    # Pages deploy should have 10-minute timeout
    assert pages_config["jobs"]["deploy"]["timeout-minutes"] == 10, (
        "Pages deploy job should have 10-minute timeout"
    )
