"""Tests that verify all examples work correctly."""

import asyncio
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pytest
import svcs

from svcs_di import DefaultInjector, Inject, Injector, KeywordInjector, auto, auto_async

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def get_example_files():
    """Get all Python example files (excluding subdirectories for now)."""
    return sorted(EXAMPLES_DIR.glob("*.py"))


def get_keyword_example_files():
    """Get all Python example files in keyword subdirectory."""
    keyword_dir = EXAMPLES_DIR / "keyword"
    if keyword_dir.exists():
        return sorted(keyword_dir.glob("*.py"))
    return []


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


@pytest.mark.parametrize(
    "example_file", get_keyword_example_files(), ids=lambda p: p.name
)
def test_keyword_example_runs_without_error(example_file):
    """Test that each keyword example runs without errors."""
    result = subprocess.run(
        [sys.executable, str(example_file)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, (
        f"Keyword example {example_file.name} failed with return code {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )

    # All examples should produce some output
    assert result.stdout, f"Keyword example {example_file.name} produced no output"


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


def test_keyword_first_example():
    """Test keyword/first_example.py produces expected output."""
    result = subprocess.run(
        [sys.executable, str(EXAMPLES_DIR / "keyword" / "first_example.py")],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Case 1: Normal usage" in result.stdout
    assert "Case 2: Override timeout via kwargs" in result.stdout
    assert "Case 3: Override Inject db for testing" in result.stdout
    assert "Case 4: Register KeywordInjector as custom injector" in result.stdout
    assert "Case 5: Kwargs validation" in result.stdout
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


# ============================================================================
# Strategic test coverage for critical edge cases and error conditions
# ============================================================================


def test_missing_dependency_raises_error():
    """Test that missing Inject dependency raises appropriate error.

    Critical workflow: Attempting to resolve a service when its Inject
    dependency is not registered should fail with a clear error.
    """

    @dataclass
    class Database:
        host: str = "localhost"

    @dataclass
    class Service:
        db: Inject[Database]

    registry = svcs.Registry()
    # Intentionally NOT registering Database
    registry.register_factory(Service, auto(Service))

    container = svcs.Container(registry)

    # Should raise ServiceNotFoundError when trying to inject Database
    with pytest.raises(svcs.exceptions.ServiceNotFoundError):
        container.get(Service)


def test_multiple_injectable_dependencies():
    """Test service with multiple Inject parameters.

    Critical workflow: Services often depend on multiple other services.
    Verify all Inject dependencies are resolved correctly.
    """

    @dataclass
    class Database:
        host: str = "db.example.com"

    @dataclass
    class Cache:
        max_size: int = 100

    @dataclass
    class Logger:
        level: str = "INFO"

    @dataclass
    class ComplexService:
        db: Inject[Database]
        cache: Inject[Cache]
        logger: Inject[Logger]
        timeout: int = 30

    registry = svcs.Registry()
    registry.register_factory(Database, auto(Database))
    registry.register_factory(Cache, auto(Cache))
    registry.register_factory(Logger, auto(Logger))
    registry.register_factory(ComplexService, auto(ComplexService))

    container = svcs.Container(registry)
    service = container.get(ComplexService)

    assert service.db.host == "db.example.com"  # type: ignore[attr-defined]
    assert service.cache.max_size == 100  # type: ignore[attr-defined]
    assert service.logger.level == "INFO"  # type: ignore[attr-defined]
    assert service.timeout == 30


def test_kwargs_override_with_keyword_injector():
    """Test that KeywordInjector enables kwargs override for testing.

    This test demonstrates migrating from DefaultInjector to KeywordInjector
    for kwargs override support.
    """

    @dataclass
    class Database:
        host: str

    @dataclass
    class MockDatabase:
        host: str

    @dataclass
    class Service:
        db: Inject[Database]

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="prod"))

    container = svcs.Container(registry)
    injector = KeywordInjector(container=container)

    # Override with different type using KeywordInjector - duck typing works
    mock_db = MockDatabase(host="mock")
    service = injector(Service, db=mock_db)

    assert isinstance(service.db, (Database, MockDatabase))  # Type guard
    assert service.db.host == "mock"


def test_protocol_with_incompatible_implementation():
    """Test protocol validation with runtime checks.

    Edge case: Python's Protocol is structural, so type checkers validate
    at compile time. At runtime, if an implementation is missing methods,
    it will fail when those methods are called.
    """

    class ReaderProtocol(Protocol):
        def read(self) -> str: ...

    class BrokenReader:
        # Missing the read() method - not compatible
        pass

    @dataclass
    class Service:
        reader: Inject[ReaderProtocol]

    registry = svcs.Registry()
    registry.register_value(ReaderProtocol, BrokenReader())
    registry.register_factory(Service, auto(Service))

    container = svcs.Container(registry)
    service = container.get(Service)

    # Service is created successfully (structural typing at runtime)
    assert service is not None

    # But calling the protocol method fails
    with pytest.raises(AttributeError):
        service.reader.read()  # type: ignore[attr-defined]


def test_async_with_sync_get():
    """Test error when using sync get() with async dependencies.

    Critical error condition: Attempting to use container.get() when
    a service has async factories should fail appropriately.
    """

    @dataclass
    class Database:
        host: str

    async def async_db_factory() -> Database:
        await asyncio.sleep(0.001)
        return Database(host="async-host")

    @dataclass
    class Service:
        db: Inject[Database]

    registry = svcs.Registry()
    registry.register_factory(Database, async_db_factory)
    registry.register_factory(Service, auto_async(Service))

    container = svcs.Container(registry)

    # Attempting to use sync get() with async factory should fail
    with pytest.raises((RuntimeError, TypeError)):  # type: ignore[call-overload]
        container.get(Service)


def test_async_with_mixed_dependencies():
    """Test async service with both sync and async dependencies.

    Critical workflow: Services can have a mix of sync and async
    dependencies. auto_async() should handle both correctly.
    """

    @dataclass
    class SyncConfig:
        setting: str = "value"

    @dataclass
    class AsyncDatabase:
        host: str

    async def async_db_factory() -> AsyncDatabase:
        await asyncio.sleep(0.001)
        return AsyncDatabase(host="async-db")

    @dataclass
    class MixedService:
        config: Inject[SyncConfig]
        db: Inject[AsyncDatabase]

    registry = svcs.Registry()
    registry.register_factory(SyncConfig, auto(SyncConfig))
    registry.register_factory(AsyncDatabase, async_db_factory)
    registry.register_factory(MixedService, auto_async(MixedService))

    # Use anyio to run async test
    async def run_test():
        async with svcs.Container(registry) as container:
            service = await container.aget(MixedService)

            assert service.config.setting == "value"  # type: ignore[attr-defined]
            assert service.db.host == "async-db"  # type: ignore[attr-defined]

    # Run with anyio backend (already installed in project)
    import anyio

    anyio.run(run_test)


def test_custom_injector_exception_handling():
    """Test custom injector that raises exceptions.

    Edge case: Custom injectors may perform validation or other logic
    that can raise exceptions. These should propagate correctly.
    """

    @dataclass
    class StrictInjector:
        container: svcs.Container

        def __call__(self, target, **kwargs):
            # Injector that rejects certain targets
            if target.__name__ == "ForbiddenService":
                raise ValueError(f"Service {target.__name__} is not allowed")

            default = DefaultInjector(container=self.container)
            return default(target, **kwargs)

    @dataclass
    class AllowedService:
        value: int = 42

    @dataclass
    class ForbiddenService:
        value: int = 99

    registry = svcs.Registry()

    # Factory parameter named svcs_container so svcs auto-detects it
    def strict_injector_factory(svcs_container: svcs.Container) -> StrictInjector:
        return StrictInjector(container=svcs_container)

    registry.register_factory(Injector, strict_injector_factory)
    registry.register_factory(AllowedService, auto(AllowedService))
    registry.register_factory(ForbiddenService, auto(ForbiddenService))

    container = svcs.Container(registry)

    # Allowed service should work
    allowed = container.get(AllowedService)
    assert allowed.value == 42

    # Forbidden service should raise exception
    with pytest.raises(ValueError, match="not allowed"):
        container.get(ForbiddenService)


def test_nested_injectable_dependencies():
    """Test deeply nested Inject dependency chains.

    Critical workflow: Service A depends on B, B depends on C, etc.
    Verify the entire chain is resolved correctly.
    """

    @dataclass
    class ConfigLevel3:
        setting: str = "deep"

    @dataclass
    class ServiceLevel2:
        config: Inject[ConfigLevel3]

    @dataclass
    class ServiceLevel1:
        service: Inject[ServiceLevel2]

    @dataclass
    class TopService:
        service: Inject[ServiceLevel1]
        name: str = "top"

    registry = svcs.Registry()
    registry.register_factory(ConfigLevel3, auto(ConfigLevel3))
    registry.register_factory(ServiceLevel2, auto(ServiceLevel2))
    registry.register_factory(ServiceLevel1, auto(ServiceLevel1))
    registry.register_factory(TopService, auto(TopService))

    container = svcs.Container(registry)
    service = container.get(TopService)

    # Navigate the entire chain
    assert service.name == "top"
    assert service.service.service.config.setting == "deep"  # type: ignore[attr-defined]


def test_protocol_with_multiple_implementations():
    """Test swapping between multiple protocol implementations.

    Critical workflow: One of the key benefits of protocol-based injection
    is the ability to swap implementations. Verify this works correctly
    with multiple concrete implementations.
    """

    class StorageProtocol(Protocol):
        def save(self, data: str) -> None: ...

        def load(self) -> str: ...

    @dataclass
    class MemoryStorage:
        def __init__(self):
            self._data: str = ""

        def save(self, data: str) -> None:
            self._data = data

        def load(self) -> str:
            return self._data

    @dataclass
    class FileStorage:
        def __init__(self):
            self._file_data: str = "file_content"

        def save(self, data: str) -> None:
            self._file_data = data

        def load(self) -> str:
            return self._file_data

    @dataclass
    class Application:
        storage: Inject[StorageProtocol]

    # Test with MemoryStorage
    registry1 = svcs.Registry()
    registry1.register_value(StorageProtocol, MemoryStorage())
    registry1.register_factory(Application, auto(Application))

    container1 = svcs.Container(registry1)
    app1 = container1.get(Application)
    app1.storage.save("memory_data")  # type: ignore[attr-defined]
    assert app1.storage.load() == "memory_data"  # type: ignore[attr-defined]

    # Test with FileStorage
    registry2 = svcs.Registry()
    registry2.register_value(StorageProtocol, FileStorage())
    registry2.register_factory(Application, auto(Application))

    container2 = svcs.Container(registry2)
    app2 = container2.get(Application)
    assert app2.storage.load() == "file_content"  # type: ignore[attr-defined]
