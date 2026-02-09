from dataclasses import dataclass


@dataclass
class Slot:
    """Base class for openGrid slots."""


@dataclass
class Tile(Slot):
    """A slot that contains an openGrid tile."""


@dataclass
class Hole(Slot):
    """An empty slot."""
