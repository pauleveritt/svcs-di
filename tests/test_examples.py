"""Tests that verify all examples work correctly."""

import asyncio
import importlib.util
from pathlib import Path
from types import ModuleType

import anyio
import pytest

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def get_example_modules() -> list[ModuleType]:
    """Get all Python example files as imported modules, including first-level subdirectories."""
    modules: list[ModuleType] = []

    # Build list of directories to search: examples dir + first-level subdirectories
    dirs_to_search = [EXAMPLES_DIR]
    dirs_to_search.extend(
        sorted(path for path in EXAMPLES_DIR.iterdir() if path.is_dir())
    )

    # Import all .py files from all directories
    for directory in dirs_to_search:
        for py_file in sorted(directory.glob("*.py")):
            if directory == EXAMPLES_DIR:
                module_name = py_file.stem
            else:
                module_name = f"{directory.name}.{py_file.stem}"

            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                modules.append(module)

    return modules


@pytest.mark.parametrize("example_module", get_example_modules())
def test_example_runs_without_error(example_module):
    """Test that each example runs without errors."""
    # Check if module has a main function
    if not hasattr(example_module, "main"):
        pytest.skip(f"Module {example_module.__name__} has no main function")

    main_func = getattr(example_module, "main")

    # Check if main is async
    if asyncio.iscoroutinefunction(main_func):
        # Run async main
        anyio.run(main_func, tuple())
    else:
        # Run sync main
        main_func()
