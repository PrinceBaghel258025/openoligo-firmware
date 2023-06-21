"""
This module contains definitions of protocols and exceptions related to switchable devices.
"""
from typing import Callable, Protocol


class Switchable(Protocol):
    """
    This protocol represents a switchable device. Any class implementing this protocol should
    be able to set, get the current value and toggle the state of the switch.
    """

    def __init__(self, pin: int, name: str, *, on_set: Callable[[bool], None] = lambda _: None):
        """Initialize the switchable device."""
        raise NotImplementedError

    def set(self, state: bool):
        """Set the state of the switch."""
        raise NotImplementedError

    @property
    def value(self) -> bool:
        """Get the current value of the switch."""
        raise NotImplementedError


class SwitchingError(Exception):
    """
    An exception that represents a failure in switching operation.
    """


class InvalidManifoldSizeError(Exception):
    """
    An exception that represents an invalid manifold size.
    """
