# Type hinting

## Python idioms

- Aggressively use modern Python features for type hinting
- Use `type` statement for type aliases (e.g., `type Vector = list[float]`)
- Use PEP 604 union syntax (`X | Y` instead of `Union[X, Y]`), built-in generics (`list[str]` instead of `List[str]`)
- Use PEP 695 syntax `def func[T](x: T) -> T:` for generic functions
- Prefer a type hint with `| None` instead of `Optional`
- Don't use `getattr` on objects that are dataclasses to fix type hinting, trust the dataclass.
- Added TypeGuard for proper type narrowing
  - `def _should_process_href(href: str | None) -> TypeGuard[str]:`
  - Benefit: The type checker knows href is str after check
- Avoid circular imports on type hints by using the `if TYPE_CHECKING` guard