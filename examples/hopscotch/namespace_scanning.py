"""Example: scanning a namespace package (no __init__.py)."""

import examples.hopscotch.app_site as app_site
from examples.hopscotch.app_site.services import SiteService

from svcs_di.injectors import HopscotchContainer, HopscotchRegistry, scan


def main() -> SiteService:
    """Demonstrate scanning a namespace package."""
    registry = HopscotchRegistry()
    scan(registry, app_site)

    container = HopscotchContainer(registry)
    return container.inject(SiteService)


if __name__ == "__main__":
    print(main())
