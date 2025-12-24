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


def test_basic_dataclass_example():
    """Test basic_dataclass.py produces expected output."""
    result = subprocess.run(
        [sys.executable, str(EXAMPLES_DIR / "basic_dataclass.py")],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Service created with timeout=30" in result.stdout
    assert "Database host=localhost, port=5432" in result.stdout


def test_kwargs_override_example():
    """Test kwargs_override.py produces expected output."""
    result = subprocess.run(
        [sys.executable, str(EXAMPLES_DIR / "kwargs_override.py")],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Case 1: Normal usage" in result.stdout
    assert "Case 2: Override timeout via factory" in result.stdout
    assert "Case 3: Override db for testing" in result.stdout
    assert "Timeout: 30" in result.stdout
    assert "Timeout: 60" in result.stdout


def test_protocol_injection_example():
    """Test protocol_injection.py produces expected output."""
    result = subprocess.run(
        [sys.executable, str(EXAMPLES_DIR / "protocol_injection.py")],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Hello, World!" in result.stdout
    assert "Hola, Mundo!" in result.stdout


def test_async_injection_example():
    """Test async_injection.py produces expected output."""
    result = subprocess.run(
        [sys.executable, str(EXAMPLES_DIR / "async_injection.py")],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Database initialized asynchronously" in result.stdout
    assert "Service created:" in result.stdout
    assert "Database:" in result.stdout
    assert "Cache:" in result.stdout


def test_custom_injector_example():
    """Test custom_injector.py produces expected output."""
    result = subprocess.run(
        [sys.executable, str(EXAMPLES_DIR / "custom_injector.py")],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Example 1: Logging Injector" in result.stdout
    assert "[INJECTOR] Creating instance of Service" in result.stdout
    assert "[INJECTOR] Created Service successfully" in result.stdout
    assert "Example 2: Validating Injector" in result.stdout
    assert "Validation failed as expected" in result.stdout
