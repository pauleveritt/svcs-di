"""Tests for location-based service registration (Task Group 2)."""

from dataclasses import dataclass
from pathlib import PurePath

import pytest
import svcs

from svcs_di.injectors.locator import (
    FactoryRegistration,
    ServiceLocator,
)


# Test fixtures
@dataclass
class DefaultGreeting:
    salutation: str = "Hello"


@dataclass
class AdminGreeting:
    salutation: str = "Welcome Admin"


@dataclass
class PublicGreeting:
    salutation: str = "Welcome Guest"


# Service protocol
class Greeting:
    salutation: str


# Context classes
class AdminContext:
    pass


class PublicContext:
    pass


# ============================================================================
# Task 2.1: Tests for location-based registration
# ============================================================================


def test_register_service_with_location_parameter():
    """Test registering a service with location parameter (PurePath instance)."""
    locator = ServiceLocator()
    admin_location = PurePath("/admin")

    locator = locator.register(Greeting, AdminGreeting, location=admin_location)

    # Single registration uses fast path
    assert len(locator._single_registrations) == 1
    assert Greeting in locator._single_registrations
    reg = locator._single_registrations[Greeting]
    assert reg.location == admin_location
    assert reg.service_type == Greeting
    assert reg.implementation == AdminGreeting


def test_register_service_with_resource_and_location():
    """Test registering service with both resource AND location parameters."""
    locator = ServiceLocator()
    admin_location = PurePath("/admin")

    locator = locator.register(
        Greeting, AdminGreeting, resource=AdminContext, location=admin_location
    )

    # Single registration uses fast path
    assert len(locator._single_registrations) == 1
    reg = locator._single_registrations[Greeting]
    assert reg.resource == AdminContext
    assert reg.location == admin_location
    assert reg.service_type == Greeting
    assert reg.implementation == AdminGreeting


def test_location_stored_in_registration_metadata():
    """Test that location is stored in registration metadata."""
    admin_location = PurePath("/admin")
    public_location = PurePath("/public")

    reg1 = FactoryRegistration(
        service_type=Greeting,
        implementation=AdminGreeting,
        resource=None,
        location=admin_location,
    )

    reg2 = FactoryRegistration(
        service_type=Greeting,
        implementation=PublicGreeting,
        resource=None,
        location=public_location,
    )

    assert reg1.location == admin_location
    assert reg2.location == public_location

    # Test that location is None by default (backward compatibility)
    reg3 = FactoryRegistration(
        service_type=Greeting, implementation=DefaultGreeting, resource=None
    )
    assert reg3.location is None


def test_lifo_ordering_preserved_with_location():
    """Test LIFO ordering is preserved with location registrations."""
    locator = ServiceLocator()
    admin_location = PurePath("/admin")
    public_location = PurePath("/public")

    # Register in order: default -> admin -> public
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, AdminGreeting, location=admin_location)
    locator = locator.register(Greeting, PublicGreeting, location=public_location)

    # Three registrations for same service type uses multi path
    assert len(locator._multi_registrations) == 1
    assert Greeting in locator._multi_registrations
    regs = locator._multi_registrations[Greeting]
    assert len(regs) == 3

    # Verify LIFO order (most recent first)
    assert regs[0].implementation == PublicGreeting
    assert regs[0].location == public_location

    assert regs[1].implementation == AdminGreeting
    assert regs[1].location == admin_location

    assert regs[2].implementation == DefaultGreeting
    assert regs[2].location is None


def test_location_none_by_default_backward_compatibility():
    """Test that location field defaults to None for backward compatibility."""
    locator = ServiceLocator()

    # Register without location parameter
    locator = locator.register(Greeting, DefaultGreeting)

    # Single registration uses fast path
    assert len(locator._single_registrations) == 1
    assert locator._single_registrations[Greeting].location is None


def test_multiple_locations_for_same_service():
    """Test registering multiple implementations of same service at different locations."""
    locator = ServiceLocator()
    admin_location = PurePath("/admin")
    public_location = PurePath("/public")

    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, AdminGreeting, location=admin_location)
    locator = locator.register(Greeting, PublicGreeting, location=public_location)

    # All three should be registered (multi path)
    assert len(locator._multi_registrations) == 1
    assert Greeting in locator._multi_registrations
    regs = locator._multi_registrations[Greeting]
    assert len(regs) == 3

    # Verify each has correct location
    registrations_by_impl = {reg.implementation: reg.location for reg in regs}

    assert registrations_by_impl[DefaultGreeting] is None
    assert registrations_by_impl[AdminGreeting] == admin_location
    assert registrations_by_impl[PublicGreeting] == public_location


@pytest.fixture
def registry():
    """Create a fresh svcs.Registry for each test."""
    return svcs.Registry()
