"""
KeywordInjector implementation with three-tier precedence for kwargs support.

This module provides KeywordInjector and KeywordAsyncInjector which support
kwargs override functionality that was extracted from DefaultInjector.

Helper functions are imported from svcs_di.auto to maintain a standalone DefaultInjector.
"""

import dataclasses
from typing import Any

import svcs

# Import helper functions from auto.py
from svcs_di.auto import (
    FieldInfo,
    get_field_infos,
)


@dataclasses.dataclass(frozen=True)
class KeywordInjector:
    """
    Dependency injector with kwargs override support.

    Implements three-tier precedence for value resolution:
    1. kwargs passed to injector (highest priority - overrides everything)
    2. container.get(T) or container.get_abstract(T) for Injectable[T] fields
    3. default values from field definitions (lowest priority)

    This is the extracted kwargs functionality from the original DefaultInjector,
    designed to be used when kwargs override support is needed.
    """

    container: svcs.Container

    def _validate_kwargs(
        self, target: type, field_infos: list[FieldInfo], kwargs: dict[str, Any]
    ) -> None:
        """Validate that all kwargs match actual field names."""
        valid_field_names = {f.name for f in field_infos}
        for kwarg_name in kwargs:
            if kwarg_name not in valid_field_names:
                raise ValueError(
                    f"Unknown parameter '{kwarg_name}' for {target.__name__}. "
                    f"Valid parameters: {', '.join(sorted(valid_field_names))}"
                )

    def _resolve_field_value_sync(
        self, field_info: FieldInfo, kwargs: dict[str, Any]
    ) -> tuple[bool, Any]:
        """
        Resolve a single field's value using three-tier precedence.

        Returns:
            tuple[bool, Any]: (has_value, value) where has_value indicates if a value was resolved
        """
        field_name = field_info.name

        # Tier 1: kwargs (highest priority)
        if field_name in kwargs:
            return (True, kwargs[field_name])

        # Tier 2: Injectable from container
        if field_info.is_injectable:
            match field_info.inner_type:
                case None:
                    raise TypeError(
                        f"Injectable field '{field_name}' has no inner type"
                    )
                case inner_type if field_info.is_protocol:
                    return True, self.container.get_abstract(inner_type)
                case inner_type:
                    return True, self.container.get(inner_type)

        # Tier 3: default value
        if field_info.has_default:
            default_val = field_info.default_value
            if callable(default_val) and hasattr(default_val, "__self__"):
                return True, default_val()
            else:
                return True, default_val

        return (False, None)

    def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """
        Inject dependencies and construct target instance.

        Args:
            target: The class or callable to construct
            **kwargs: Keyword arguments that override any resolved dependencies

        Returns:
            An instance of target with dependencies injected

        Raises:
            ValueError: If unknown kwargs are provided
            TypeError: If an Injectable field has no inner type
        """
        field_infos = get_field_infos(target)
        self._validate_kwargs(target, field_infos, kwargs)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = self._resolve_field_value_sync(field_info, kwargs)
            if has_value:
                resolved_kwargs[field_info.name] = value

        return target(**resolved_kwargs)


@dataclasses.dataclass(frozen=True)
class KeywordAsyncInjector:
    """
    Async dependency injector with kwargs override support.

    Like KeywordInjector but uses async container methods (aget, aget_abstract)
    for resolving Injectable[T] dependencies. Wraps sync logic where possible
    to avoid code duplication.

    Implements the same three-tier precedence as KeywordInjector:
    1. kwargs passed to injector (highest priority)
    2. container.aget(T) or container.aget_abstract(T) for Injectable[T] fields
    3. default values from field definitions (lowest priority)
    """

    container: svcs.Container

    def _validate_kwargs(
        self, target: type, field_infos: list[FieldInfo], kwargs: dict[str, Any]
    ) -> None:
        """Validate that all kwargs match actual field names."""
        valid_field_names = {f.name for f in field_infos}
        for kwarg_name in kwargs:
            if kwarg_name not in valid_field_names:
                raise ValueError(
                    f"Unknown parameter '{kwarg_name}' for {target.__name__}. "
                    f"Valid parameters: {', '.join(sorted(valid_field_names))}"
                )

    async def _resolve_field_value_async(
        self, field_info: FieldInfo, kwargs: dict[str, Any]
    ) -> tuple[bool, Any]:
        """
        Async version of field value resolution with three-tier precedence.

        Returns:
            tuple[bool, Any]: (has_value, value) where has_value indicates if a value was resolved
        """
        field_name = field_info.name

        # Tier 1: kwargs (highest priority)
        if field_name in kwargs:
            return (True, kwargs[field_name])

        # Tier 2: Injectable from container (async)
        if field_info.is_injectable:
            match field_info.inner_type:
                case None:
                    raise TypeError(
                        f"Injectable field '{field_name}' has no inner type"
                    )
                case inner_type if field_info.is_protocol:
                    return True, await self.container.aget_abstract(inner_type)
                case inner_type:
                    return True, await self.container.aget(inner_type)

        # Tier 3: default value
        if field_info.has_default:
            default_val = field_info.default_value
            if callable(default_val) and hasattr(default_val, "__self__"):
                return True, default_val()
            else:
                return True, default_val

        return (False, None)

    async def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """
        Async inject dependencies and construct target instance.

        Args:
            target: The class or callable to construct
            **kwargs: Keyword arguments that override any resolved dependencies

        Returns:
            An instance of target with dependencies injected

        Raises:
            ValueError: If unknown kwargs are provided
            TypeError: If an Injectable field has no inner type
        """
        field_infos = get_field_infos(target)
        self._validate_kwargs(target, field_infos, kwargs)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = await self._resolve_field_value_async(field_info, kwargs)
            if has_value:
                resolved_kwargs[field_info.name] = value

        return target(**resolved_kwargs)
