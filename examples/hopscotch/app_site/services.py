"""Services in a namespace package."""

from dataclasses import dataclass

from svcs_di.injectors import injectable


@injectable
@dataclass
class SiteService:
    """A service in the app_site namespace package."""

    name: str = "SiteService"
