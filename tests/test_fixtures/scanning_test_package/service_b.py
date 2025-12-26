"""Another module with decorated services for scanning tests."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable


class CustomerContext:
    pass


@injectable(resource=CustomerContext)
@dataclass
class ServiceB:
    name: str = "ServiceB"
