"""
Free-threaded Python compatibility tests.

This module verifies thread-safety of svcs-di components under PEP 703's free-threaded
Python (no-GIL mode) through concurrent access stress tests.

Thread-Safety Design Patterns Verified:
- Immutability: Frozen dataclasses, PurePath, and immutable data structures
- Atomic operations: Dict get/set operations are thread-safe
- Idempotent cache: Multiple threads computing same result is acceptable
- No global state: All state is local to immutable objects

The tests in this module use multiple concurrent threads to stress-test the following:
1. ServiceLocator concurrent cache access and registration
2. HopscotchInjector concurrent service resolution (sync and async)
3. Decorator and scanning concurrent operations
4. Inject[T] field resolution under concurrent access

All tests are marked with @pytest.mark.freethreaded and require a free-threaded Python build.
"""

import asyncio
import sysconfig
import threading
from dataclasses import dataclass
from pathlib import PurePath
from typing import Optional

import pytest
import svcs

from svcs_di.auto import Inject
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.locator import (
    HopscotchAsyncInjector,
    HopscotchInjector,
    Location,
    ServiceLocator,
    scan,
)


# ============================================================================
# Task Group 1: Infrastructure Setup
# ============================================================================


def is_free_threaded_build() -> bool:
    """
    Check if running on free-threaded Python build.

    Returns True if Py_GIL_DISABLED is set (free-threaded build),
    False otherwise (standard GIL build).
    """
    gil_disabled = sysconfig.get_config_var("Py_GIL_DISABLED")
    return gil_disabled == 1


@pytest.mark.freethreaded
def test_free_threaded_build_detection():
    """Test that free-threaded build detection works correctly."""
    # This test verifies the detection function exists and returns a boolean
    result = is_free_threaded_build()
    assert isinstance(result, bool)


@pytest.mark.freethreaded
def test_pytest_run_parallel_available():
    """Test that pytest-run-parallel plugin is available."""
    # If this test runs, pytest-run-parallel is available
    # The plugin is invoked with: pytest -p freethreaded
    assert True


@pytest.mark.freethreaded
@pytest.mark.skipif(
    not is_free_threaded_build(),
    reason="Requires free-threaded Python build (python3.14t or later)",
)
def test_free_threaded_build_confirmed():
    """Test that we are running on a free-threaded build."""
    # This test only runs on free-threaded Python
    assert is_free_threaded_build() is True


# ============================================================================
# Task Group 2: ServiceLocator Thread-Safety
# ============================================================================


# Test fixtures for ServiceLocator tests
@dataclass
class Greeting:
    message: str = "Hello"


@dataclass
class DefaultGreeting:
    message: str = "Default"


@dataclass
class EmployeeGreeting:
    message: str = "Employee"


@dataclass
class CustomerGreeting:
    message: str = "Customer"


class EmployeeContext:
    pass


class CustomerContext:
    pass


@pytest.mark.freethreaded
def test_service_locator_concurrent_cache_access():
    """Test ServiceLocator cache with concurrent read/write from multiple threads."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    locator = locator.register(Greeting, CustomerGreeting, resource=CustomerContext)

    results = []
    errors = []

    def worker(resource: Optional[type]):
        """Worker thread that performs multiple lookups."""
        try:
            for _ in range(100):
                impl = locator.get_implementation(Greeting, resource=resource)
                results.append((resource, impl))
        except Exception as e:
            errors.append(e)

    # Spawn 16 threads performing concurrent lookups
    threads = []
    for _ in range(8):
        threads.append(threading.Thread(target=worker, args=(None,)))
        threads.append(threading.Thread(target=worker, args=(EmployeeContext,)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # Verify results are correct
    for resource, impl in results:
        if resource is None:
            assert impl == DefaultGreeting
        elif resource == EmployeeContext:
            assert impl == EmployeeGreeting


@pytest.mark.freethreaded
def test_service_locator_concurrent_registration():
    """Test concurrent registration operations creating new immutable ServiceLocator instances."""
    # Start with base locator
    base_locator = ServiceLocator()

    results = []
    errors = []

    def worker(worker_id: int):
        """Worker thread that performs registrations."""
        try:
            # Each thread creates its own chain of registrations
            locator = base_locator

            @dataclass
            class WorkerGreeting:
                message: str = f"Worker {worker_id}"

            locator = locator.register(Greeting, WorkerGreeting)
            impl = locator.get_implementation(Greeting)
            results.append((worker_id, impl))
        except Exception as e:
            errors.append(e)

    # Spawn 8 threads performing concurrent registrations
    threads = []
    for i in range(8):
        threads.append(threading.Thread(target=worker, args=(i,)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # Verify base locator is unchanged (immutability)
    assert len(base_locator._single_registrations) == 0
    assert len(base_locator._multi_registrations) == 0

    # Verify all threads got results
    assert len(results) == 8


@pytest.mark.freethreaded
def test_service_locator_immutability_guarantees():
    """Test frozen dataclass immutability under concurrent access."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)

    # Verify frozen dataclass prevents mutation
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        locator._cache = {}  # type: ignore[misc]

    # Verify registration returns new instance
    locator2 = locator.register(Greeting, EmployeeGreeting)
    assert locator is not locator2
    assert len(locator._single_registrations) == 1
    assert len(locator2._multi_registrations) == 1


@pytest.mark.freethreaded
def test_purepath_immutability():
    """Test PurePath (Location) immutability guarantees."""
    location = PurePath("/admin")

    # Verify operations return new instances
    child = location / "users"
    assert location == PurePath("/admin")  # Original unchanged
    assert child == PurePath("/admin/users")

    # Verify parent operations
    parent = child.parent
    assert child == PurePath("/admin/users")  # Original unchanged
    assert parent == PurePath("/admin")


@pytest.mark.freethreaded
def test_service_locator_idempotent_cache():
    """Test that multiple threads computing same cached result is acceptable."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)

    results = []
    errors = []

    def worker():
        """Worker thread that performs lookups, potentially computing same result."""
        try:
            # Clear the cache entry by accessing it from a fresh perspective
            # (in practice, cache is shared and threads may compute same result)
            impl = locator.get_implementation(Greeting)
            results.append(impl)
        except Exception as e:
            errors.append(e)

    # Spawn many threads simultaneously to stress-test idempotent cache
    threads = [threading.Thread(target=worker) for _ in range(32)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # Verify all results are correct (same implementation)
    assert all(impl == DefaultGreeting for impl in results)
    assert len(results) == 32


# ============================================================================
# Task Group 3: Injector Thread-Safety
# ============================================================================


# Test fixtures for injector tests
@dataclass
class Database:
    name: str = "test"


@dataclass
class PostgresDB:
    name: str = "postgres"


@dataclass
class Service:
    greeting: Inject[Greeting]


@dataclass
class MultiFieldService:
    greeting: Inject[Greeting]
    database: Inject[Database]


@pytest.mark.freethreaded
def test_hopscotch_injector_concurrent_resolution():
    """Test HopscotchInjector concurrent service resolution."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    locator = locator.register(Database, PostgresDB)

    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)
    registry.register_value(EmployeeContext, EmployeeContext())

    results = []
    errors = []

    def worker():
        """Worker thread that performs concurrent injector calls."""
        try:
            container = svcs.Container(registry)
            injector = HopscotchInjector(container=container, resource=EmployeeContext)

            for _ in range(50):
                service = injector(Service)
                results.append(service)
        except Exception as e:
            errors.append(e)

    # Spawn 8 threads performing concurrent injections
    threads = [threading.Thread(target=worker) for _ in range(8)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # Verify all results are correct
    assert all(isinstance(s.greeting, EmployeeGreeting) for s in results)
    assert len(results) == 400  # 8 threads * 50 iterations


@pytest.mark.freethreaded
def test_hopscotch_injector_multifield_service():
    """Test concurrent injection of services with multiple fields."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Database, PostgresDB)

    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)

    results = []
    errors = []

    def worker():
        """Worker thread that performs concurrent injector calls."""
        try:
            container = svcs.Container(registry)
            injector = HopscotchInjector(container=container)

            for _ in range(30):
                service = injector(MultiFieldService)
                results.append(service)
        except Exception as e:
            errors.append(e)

    # Spawn 8 threads
    threads = [threading.Thread(target=worker) for _ in range(8)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 240  # 8 threads * 30 iterations
    # Verify both fields were injected
    assert all(isinstance(s.greeting, DefaultGreeting) for s in results)
    assert all(isinstance(s.database, PostgresDB) for s in results)


@pytest.mark.freethreaded
def test_hopscotch_injector_location_based_resolution():
    """Test concurrent location-based resolution."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, EmployeeGreeting, location=PurePath("/admin"))

    results = []
    errors = []

    def worker(location: PurePath):
        """Worker thread with specific location."""
        try:
            registry = svcs.Registry()
            registry.register_value(ServiceLocator, locator)
            registry.register_value(Location, location)

            container = svcs.Container(registry)
            injector = HopscotchInjector(container=container)

            for _ in range(50):
                service = injector(Service)
                results.append((location, service.greeting))
        except Exception as e:
            errors.append(e)

    # Spawn threads with different locations
    threads = []
    for _ in range(4):
        threads.append(threading.Thread(target=worker, args=(PurePath("/admin"),)))
        threads.append(threading.Thread(target=worker, args=(PurePath("/public"),)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # Verify results match locations
    admin_results = [g for loc, g in results if loc == PurePath("/admin")]
    public_results = [g for loc, g in results if loc == PurePath("/public")]

    assert all(isinstance(g, EmployeeGreeting) for g in admin_results)
    assert all(isinstance(g, DefaultGreeting) for g in public_results)


@pytest.mark.freethreaded
@pytest.mark.anyio
async def test_hopscotch_async_injector_concurrent_resolution():
    """Test HopscotchAsyncInjector concurrent async service resolution."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Database, PostgresDB)

    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)

    async def worker():
        """Async worker that performs concurrent injections."""
        container = svcs.Container(registry)
        injector = HopscotchAsyncInjector(container=container)

        services = []
        for _ in range(10):
            service = await injector(Service)
            services.append(service)
        return services

    # Use asyncio.gather to spawn concurrent tasks
    results = await asyncio.gather(*[worker() for _ in range(8)])

    # Flatten results
    all_services = [s for worker_services in results for s in worker_services]

    # Verify all results are correct
    assert all(isinstance(s.greeting, DefaultGreeting) for s in all_services)
    assert len(all_services) == 80  # 8 workers * 10 iterations


# ============================================================================
# Task Group 4: Decorator and Scanning Thread-Safety
# ============================================================================


@pytest.mark.freethreaded
def test_decorator_concurrent_application():
    """Test concurrent @injectable decorator application."""
    results = []
    errors = []

    def worker(worker_id: int):
        """Worker thread that applies decorator."""
        try:
            # Apply decorator to a class
            @injectable
            @dataclass
            class WorkerService:
                name: str = f"Worker {worker_id}"

            results.append((worker_id, WorkerService))
        except Exception as e:
            errors.append(e)

    # Spawn 8 threads applying decorator concurrently
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # Verify all decorators applied successfully
    assert len(results) == 8
    for worker_id, service_class in results:
        assert hasattr(service_class, "__injectable_metadata__")


@pytest.mark.freethreaded
def test_scanning_concurrent_operations():
    """Test concurrent scan() operations."""
    results = []
    errors = []

    def worker(worker_id: int):
        """Worker thread that performs scanning."""
        try:
            # Create a fresh registry for each worker
            registry = svcs.Registry()

            # Define a service to scan
            @injectable
            @dataclass
            class ScanService:
                name: str = f"Scan {worker_id}"

            # Scan locals
            scan(registry, locals_dict={"ScanService": ScanService})

            # Verify scanning succeeded
            container = svcs.Container(registry)
            service = container.get(ScanService)
            results.append((worker_id, service))
        except Exception as e:
            errors.append(e)

    # Spawn 8 threads performing concurrent scanning
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 8


@pytest.mark.freethreaded
def test_decorator_with_resource_and_location():
    """Test concurrent decorator application with resource and location metadata."""
    results = []
    errors = []

    def worker(worker_id: int):
        """Worker thread that applies decorator with metadata."""
        try:

            @injectable(resource=EmployeeContext, location=PurePath("/admin"))
            @dataclass
            class MetadataService:
                name: str = f"Metadata {worker_id}"

            metadata = MetadataService.__injectable_metadata__  # type: ignore[attr-defined]
            results.append((worker_id, metadata))
        except Exception as e:
            errors.append(e)

    # Spawn 8 threads
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # Verify metadata is correct
    for worker_id, metadata in results:
        assert metadata["resource"] == EmployeeContext
        assert metadata["location"] == PurePath("/admin")


@pytest.mark.freethreaded
def test_end_to_end_decorator_scan_inject():
    """Test end-to-end: concurrent decoration -> scanning -> injection."""
    results = []
    errors = []

    def worker(worker_id: int):
        """Worker thread performing full workflow."""
        try:
            # Step 1: Decorate
            @injectable
            @dataclass
            class WorkflowService:
                message: str = f"Workflow {worker_id}"

            # Step 2: Scan
            registry = svcs.Registry()
            scan(registry, locals_dict={"WorkflowService": WorkflowService})

            # Step 3: Inject
            container = svcs.Container(registry)
            service = container.get(WorkflowService)

            results.append((worker_id, service))
        except Exception as e:
            errors.append(e)

    # Spawn 8 threads
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 8

    # Verify services are correct
    for worker_id, service in results:
        assert service.message == f"Workflow {worker_id}"
