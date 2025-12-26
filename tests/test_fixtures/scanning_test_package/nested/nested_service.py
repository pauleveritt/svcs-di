"""Nested module with decorated service."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable


@injectable
@dataclass
class NestedService:
    name: str = "NestedService"
