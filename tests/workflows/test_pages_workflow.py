"""Tests for GitHub Pages deployment workflow configuration.

These tests verify the structure and behavior of the documentation deployment workflow.
They focus on critical configuration aspects without testing GitHub Actions internals.
"""

import yaml
from pathlib import Path


def test_pages_workflow_exists():
    """Verify that the Pages workflow file exists."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )
    assert workflow_path.exists(), "Pages workflow file should exist"


def test_pages_workflow_valid_yaml():
    """Verify that the Pages workflow is valid YAML."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)
    assert config is not None, "Pages workflow should be valid YAML"
    assert isinstance(config, dict), "Pages workflow should be a dictionary"


def test_pages_workflow_triggers():
    """Verify that the Pages workflow triggers on push to main and workflow_dispatch."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)

    # The "on" key might be parsed as True (boolean) or "on" depending on YAML parser
    on_config = config.get(True, config.get("on", {}))
    assert isinstance(on_config, dict), "Pages workflow 'on' should be a dictionary"

    # Check for push trigger with main branch
    push_config = on_config.get("push", {})
    assert "branches" in push_config, "Pages workflow push should specify branches"
    assert "main" in push_config["branches"], (
        "Pages workflow should trigger on push to main"
    )

    # Check for workflow_dispatch trigger
    assert "workflow_dispatch" in on_config, (
        "Pages workflow should support manual dispatch"
    )


def test_pages_workflow_permissions():
    """Verify that the Pages workflow has correct permissions for GitHub Pages."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)

    permissions = config.get("permissions", {})
    assert permissions.get("contents") == "read", (
        "Pages workflow should have contents: read"
    )
    assert permissions.get("pages") == "write", (
        "Pages workflow should have pages: write"
    )
    assert permissions.get("id-token") == "write", (
        "Pages workflow should have id-token: write"
    )


def test_pages_workflow_concurrency():
    """Verify that the Pages workflow has concurrency controls."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)

    concurrency = config.get("concurrency", {})
    assert concurrency.get("group") == "pages", (
        "Pages workflow should use 'pages' concurrency group"
    )
    assert concurrency.get("cancel-in-progress") is False, (
        "Pages workflow should not cancel in-progress deployments"
    )


def test_pages_workflow_build_job():
    """Verify that the Pages workflow has a build job with correct steps."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)

    jobs = config.get("jobs", {})
    build_job = jobs.get("build", {})

    assert build_job is not None, "Pages workflow should have a build job"
    assert build_job.get("runs-on") == "ubuntu-latest", (
        "Build job should run on ubuntu-latest"
    )
    assert build_job.get("timeout-minutes") == 30, (
        "Build job should have 30-minute timeout"
    )

    steps = build_job.get("steps", [])
    assert len(steps) > 0, "Build job should have steps"

    # Check for key steps
    step_names = [step.get("name", "").lower() for step in steps]
    assert any("checkout" in step.get("uses", "") for step in steps), (
        "Build job should checkout repository"
    )
    assert any("just" in name for name in step_names), "Build job should install just"
    assert any(step.get("run", "") == "just docs-build" for step in steps), (
        "Build job should run 'just docs-build'"
    )
    assert any(
        "upload" in step.get("uses", "") and "pages-artifact" in step.get("uses", "")
        for step in steps
    ), "Build job should upload pages artifact"


def test_pages_workflow_deploy_job():
    """Verify that the Pages workflow has a deploy job that depends on build."""
    workflow_path = (
        Path(__file__).parent.parent.parent / ".github" / "workflows" / "pages.yml"
    )
    with open(workflow_path) as f:
        config = yaml.safe_load(f)

    jobs = config.get("jobs", {})
    deploy_job = jobs.get("deploy", {})

    assert deploy_job is not None, "Pages workflow should have a deploy job"
    assert "build" in deploy_job.get("needs", []), (
        "Deploy job should depend on build job"
    )
    assert deploy_job.get("runs-on") == "ubuntu-latest", (
        "Deploy job should run on ubuntu-latest"
    )
    assert deploy_job.get("timeout-minutes") == 10, (
        "Deploy job should have 10-minute timeout"
    )

    # Check environment configuration
    environment = deploy_job.get("environment", {})
    assert environment.get("name") == "github-pages", (
        "Deploy job should use github-pages environment"
    )

    # Check for deploy step
    steps = deploy_job.get("steps", [])
    assert len(steps) > 0, "Deploy job should have steps"
    assert any("deploy-pages" in step.get("uses", "") for step in steps), (
        "Deploy job should use deploy-pages action"
    )
