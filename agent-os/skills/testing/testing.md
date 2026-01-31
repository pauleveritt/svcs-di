---
description:
  Testing standards for Python projects. Use this when writing tests, setting
  up pytest, or reviewing test coverage.
allowed-tools: Bash(uv run pytest*)
---

# Testing Standards

## General Guidelines

*ALWAYS* run pytest via `uv run pytest`. Don't run `python` or `pytest` directly.

For detailed pytest fixture patterns, see [fixture-recipes.md](fixture-recipes.md).

## Test Structure

- **Write tests as functions, NOT classes** - Do not use `class TestFoo:` style. Write standalone `def test_foo():` functions
- Place tests in `tests/` directory
- Use descriptive function names: `test_<functionality>_<scenario>`
- Organize test module names to match the module being tested
- Test both the happy path and edge cases
- Use `tests/conftest.py` and fixtures as appropriate (but only when useful)
- When you create fixtures, write tests for those fixtures

**Example - Correct:**
```python
def test_user_can_login_with_valid_credentials() -> None:
    """Test successful login."""
    ...

def test_user_cannot_login_with_invalid_password() -> None:
    """Test login failure with wrong password."""
    ...
```

**Example - WRONG (do not do this):**
```python
class TestUserLogin:
    def test_valid_credentials(self) -> None:
        ...
    def test_invalid_password(self) -> None:
        ...
```

## Coverage Philosophy

- Don't write too many tests
- Try hard to consolidate tests
- Keep coverage at 100% as part of final verification
- Prefer unit tests but write integration tests where needed

## Test Writing Best Practices

- **Write Minimal Tests During Development**: Focus on completing the feature first, then add strategic tests
- **Test Only Core User Flows**: Write tests exclusively for critical paths and primary workflows
- **Defer Edge Case Testing**: Don't test edge cases unless business-critical
- **Test Behavior, Not Implementation**: Focus on what the code does, not how it does it
- **Clear Test Names**: Use descriptive names explaining what's being tested and expected outcome
- **Mock External Dependencies**: Isolate units by mocking databases, APIs, file systems
- **Fast Execution**: Keep unit tests fast (milliseconds)

## Pytest Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "src", "docs"]
python_files = ["test_*.py"]
addopts = "-p no:doctest -p no:freethreaded -m \"not slow\""
pythonpath = ["examples"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
timeout = 60
faulthandler_timeout = 120
```

## Service Testing with Fakes

Create simple, predictable test doubles that implement the protocol.

See [../examples/fake_database.py](../examples/fake_database.py) for the full example.

```python
@dataclass
class FakeDatabase:
    """Fake database for testing - predictable, no side effects."""
    _query_results: dict[str, list[dict]]

    def query(self, sql: str) -> list[dict]:
        return self._query_results.get(sql, [])

def test_service_with_fake():
    fake_db = FakeDatabase(_query_results={"SELECT * FROM users": [{"id": 1}]})
    service = MyService(db=fake_db)
    assert len(service.get_users()) == 1
```

**Why fakes over mocks**:
- Simple to understand and maintain
- No mock framework magic
- Tests are more resilient to refactoring
- Follows the dependency chain naturally

## Component and View Testing (tdom)

### Unit tests

- A view/component should render to an `tdom.Element` or occasionally a `tdom.Fragment`
- Use HTML template: `html(t'''<div>...</div>''')`
- Use type guard to narrow `tdom.Node` to `tdom.Element`

### aria-testing

- Prefer testing using aria-testing on an `Element`, not conversion to a string
- Use the queries in aria-testing to make assertions about what should be in the result
- Prefer finding elements via accessibility landmarks

### Storyville

Storyville is the **primary** approach for testing tdom components and views:

- Use Storyville and a `stories.py` file alongside the component/view, in the same directory
- Use the `assertions` field on a `Story` with a list of `aria-testing.assertions` helpers such as `GetByRole`
- Make sure `pyproject.toml` has `[tool.storyville.pytest]` set to `enabled = true`
- **Only write unit tests for helper functions** - component rendering should be tested via Storyville
- Place any unit tests in `tests/components/*` or `tests/views/*` with all the other tests

## Pytest Fixtures Best Practices

### Fixture Scopes

Choose the appropriate scope based on setup cost and test isolation needs:

```python
# Function scope (default) - fresh for each test
@pytest.fixture
def user():
    return create_test_user()

# Module scope - shared within a test file
@pytest.fixture(scope="module")
def database():
    db = create_database()
    yield db
    db.cleanup()

# Session scope - shared across all tests (use sparingly)
@pytest.fixture(scope="session")
def app_config():
    return load_test_config()
```

### Parametrized Fixtures

Test multiple scenarios with a single fixture:

```python
@pytest.fixture(params=["admin", "user", "guest"])
def user_role(request):
    """Test with different user roles."""
    return create_user(role=request.param)

def test_permissions(user_role):
    # Runs 3 times with different roles
    assert user_role.can_login()
```

### Factory Fixtures

Use factories when tests need customized instances:

```python
@pytest.fixture
def create_order():
    """Factory for creating orders with cleanup."""
    created = []

    def _create(user, items=None):
        order = Order(user=user, items=items or [])
        created.append(order)
        return order

    yield _create

    for order in created:
        order.delete()

def test_order_total(create_order):
    order = create_order(user=test_user, items=[item1, item2])
    assert order.total == 100
```

### Fixture Composition

Build complex fixtures from simpler ones:

```python
@pytest.fixture
def database():
    return create_database()

@pytest.fixture
def user_repo(database):
    return UserRepository(database)

@pytest.fixture
def auth_service(user_repo):
    return AuthService(user_repo)
```

## Anti-Patterns

- Using test classes (`class TestFoo:`) instead of test functions
- Using mock frameworks unless absolutely necessary
- Creating complex fakes with lots of state
- Testing svcs container mechanics in business logic tests
- Mocking the service under test itself
- Over-scoping fixtures (session scope when function scope would work)
- Fixtures with hidden side effects or dependencies

## Related Skills

- [workflow](../workflow/workflow.md) - Development lifecycle
- [svcs](../svcs.md) - Service testing patterns
- [tdom](../tdom.md) - Component testing with aria-testing
- [sybil](../sybil.md) - Doctest integration
