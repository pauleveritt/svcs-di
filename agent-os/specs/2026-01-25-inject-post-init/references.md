# References: Inject in Post Init

## Python Documentation

### dataclasses.InitVar
- **URL:** https://docs.python.org/3/library/dataclasses.html#init-only-variables
- **Key points:**
  - `InitVar[T]` creates init-only variables
  - Not stored as instance attributes
  - Passed to `__post_init__` in field order
  - `dataclasses.fields()` excludes InitVar fields

### get_type_hints
- **URL:** https://docs.python.org/3/library/typing.html#typing.get_type_hints
- **Key points:**
  - Returns all annotations including InitVar
  - Resolves forward references

### get_origin / get_args
- **URL:** https://docs.python.org/3/library/typing.html#typing.get_origin
- **Key points:**
  - `get_origin(InitVar[T])` returns `InitVar`
  - `get_args(InitVar[T])` returns `(T,)`

## Existing Code References

### svcs_di/auto.py
- `FieldInfo` NamedTuple: lines 240-249
- `_create_field_info()`: lines 274-298
- `_get_dataclass_field_infos()`: lines 345-374
- `is_injectable()`: lines 257-259
- `extract_inner_type()`: lines 262-266

### svcs.md skill
- `__post_init__` with `InitVar` pattern: lines 100-137
- Shows the pattern we're enabling with automatic injection

## Similar Patterns in Other DI Frameworks

### FastAPI Depends
- Uses `Depends()` marker for injection
- No direct InitVar support

### Python inject
- Uses decorators for injection
- No direct InitVar support

### Our Approach
- Unique: `InitVar[Inject[T]]` combines dataclass init-only vars with DI
- Natural extension of existing `Inject[T]` pattern
