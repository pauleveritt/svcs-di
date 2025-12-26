"""Module with decorated services for scanning tests."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable


@injectable
@dataclass
class ServiceA:
    name: str = "ServiceA"


@injectable
@dataclass
class AnotherServiceA:
    name: str = "AnotherServiceA"
