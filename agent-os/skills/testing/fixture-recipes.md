# Pytest Fixture Recipes

This reference provides common pytest fixture patterns for Python projects.

## Fixture Scopes

### Function Scope (Default)

Fresh instance for each test function:

```python
@pytest.fixture
def db_connection():
    """Fresh connection for each test."""
    conn = create_connection()
    yield conn
    conn.close()
```

### Module Scope

Shared across all tests in a module:

```python
@pytest.fixture(scope="module")
def expensive_resource():
    """Shared within module - use for expensive setup."""
    resource = load_large_dataset()
    yield resource
    resource.cleanup()
```

### Session Scope

Shared across entire test session:

```python
@pytest.fixture(scope="session")
def docker_container():
    """Shared across all tests - use sparingly."""
    container = start_container()
    yield container
    container.stop()
```

## Parametrized Fixtures

### Basic Parametrization

```python
@pytest.fixture(params=["sqlite", "postgresql"])
def database(request):
    """Run tests with multiple database backends."""
    db = create_database(request.param)
    yield db
    db.teardown()
```

### Named Parameters

```python
@pytest.fixture(params=[
    pytest.param("admin", id="admin-user"),
    pytest.param("guest", id="guest-user"),
])
def user_role(request):
    """Test with different user roles."""
    return create_user(role=request.param)
```

## Factory Fixtures

### Simple Factory

```python
@pytest.fixture
def create_user():
    """Factory for creating test users."""
    created_users = []

    def _create_user(name: str = "test", email: str | None = None):
        user = User(name=name, email=email or f"{name}@test.com")
        created_users.append(user)
        return user

    yield _create_user

    # Cleanup all created users
    for user in created_users:
        user.delete()
```

### Factory with Dependencies

```python
@pytest.fixture
def create_order(db_session, create_user):
    """Factory that uses other fixtures."""
    def _create_order(user=None, items=None):
        if user is None:
            user = create_user()
        order = Order(user=user, items=items or [])
        db_session.add(order)
        return order
    return _create_order
```

## Fixture Composition

### Layered Fixtures

```python
@pytest.fixture
def base_config():
    """Base configuration."""
    return {"debug": True, "log_level": "INFO"}

@pytest.fixture
def test_config(base_config):
    """Test-specific configuration extending base."""
    return {**base_config, "database": "test.db"}

@pytest.fixture
def app(test_config):
    """Application with test configuration."""
    return create_app(test_config)
```

### Request-Aware Fixtures

```python
@pytest.fixture
def resource(request):
    """Fixture that adapts based on test markers."""
    if request.node.get_closest_marker("slow"):
        return create_full_resource()
    return create_minimal_resource()
```

## Async Fixtures

```python
import pytest_asyncio

@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client fixture."""
    async with httpx.AsyncClient() as client:
        yield client
```

## Autouse Fixtures

```python
@pytest.fixture(autouse=True)
def reset_environment():
    """Automatically runs before each test."""
    os.environ.clear()
    os.environ.update(DEFAULT_ENV)
    yield
    os.environ.clear()
```

## conftest.py Organization

```python
# tests/conftest.py - Shared fixtures

@pytest.fixture(scope="session")
def app_config():
    """Session-scoped config shared by all tests."""
    return load_test_config()

@pytest.fixture
def client(app_config):
    """Test client for HTTP tests."""
    app = create_app(app_config)
    return TestClient(app)
```

## Anti-Patterns

- **Over-scoping**: Using session scope when function scope would work
- **Complex State**: Fixtures with mutable state shared between tests
- **Hidden Dependencies**: Fixtures that implicitly depend on other fixtures
- **Excessive Autouse**: Too many autouse fixtures slowing down tests
- **Missing Cleanup**: Forgetting yield and cleanup in fixtures with resources
