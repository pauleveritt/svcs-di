"""Module with no decorated services."""

from dataclasses import dataclass


@dataclass
class UnDecoratedService:
    name: str = "UnDecorated"
