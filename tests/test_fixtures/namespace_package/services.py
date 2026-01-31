"""Services in a namespace package (no __init__.py)."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable


@injectable
@dataclass
class NamespaceService:
    """A service in a namespace package."""

    name: str = "NamespaceService"
