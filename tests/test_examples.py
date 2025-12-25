"""Tests that verify all examples work correctly."""

import subprocess
import sys
from pathlib import Path

import pytest


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def get_example_files():
    """Get all Python example files."""
    return sorted(EXAMPLES_DIR.glob("*.py"))


@pytest.mark.parametrize("example_file", get_example_files(), ids=lambda p: p.name)
def test_example_runs_without_error(example_file):
    """Test that each example runs without errors."""
    result = subprocess.run(
        [sys.executable, str(example_file)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, (
        f"Example {example_file.name} failed with return code {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )

    # All examples should produce some output
    assert result.stdout, f"Example {example_file.name} produced no output"
