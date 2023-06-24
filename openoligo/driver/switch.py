"""
Switches can be used to control devices that can be turned on and off.
"""
import logging
import time
from dataclasses import dataclass, field

from openoligo.driver.rpi_pins import RPi
from openoligo.driver.board import Board
from openoligo.driver.types import Switchable, SwitchingError, Valvable, ValveState, ValveType


@dataclass
class BaseSwitch(Switchable):
    """
    A switch that actually controls a GPIO pin on the Raspberry Pi.

    Attributes:
        name: Name of the switch.
        gpio_pin: GPIO pin number.
        board: Board object to access the GPIO pins.
    """

    name: str
    gpio_pin: RPi
    board: Board
    _switch_count: int = field(default=0, init=False)
    _state: bool = field(default=False, init=False)

    def set(self, state: bool):
        """Set state of the switch ON or OFF."""
        self._state = state
        self._switch_count += 1
        self.board.set(self.gpio_pin, state)
        logging.info("Switch (%s) set to [bold]%s[/]", self.name, state, extra={"markup": True})

    @property
    def value(self) -> bool:
        """
        Get the current value of the switch.

        raises:
            SwitchingError: If the switch is not set.
        """
        if self._state is not self.board.value(self.gpio_pin):
            raise SwitchingError(f"Switch ({self.name}) is not set")
        return self._state


@dataclass
class BaseValve(Valvable):
    """
    This class represents a simulated valve. It is useful for testing purposes.
    """

    pin: int
    name: str
    gpio_pin: RPi
    board: Board
    valve_type: ValveType = field(default=ValveType.NORMALLY_OPEN)
    _switch_count: int = field(init=False, default=0)
    _state: ValveState = field(init=False)

    def __post_init__(self):
        """Initialize the valve."""
        self._state = (
            ValveState.CLOSED_FLOW
            if self.valve_type == ValveType.NORMALLY_CLOSED
            else ValveState.OPEN_FLOW
        )

    def open(self):
        """Open the valve."""
        self.set(True)

    def close(self):
        """Close the valve."""
        self.set(False)

    def set(self, state: bool):
        """Set the state of the valve."""
        self._state = ValveState.OPEN_FLOW if state else ValveState.CLOSED_FLOW
        self._switch_count += 1
        logging.debug(
            "Valve (%s) set to [bold]%s[/]", self.name, self._state, extra={"markup": True}
        )

    @property
    def value(self) -> bool:
        """Get the current value of the valve."""
        return self._state == ValveState.OPEN_FLOW

    @property
    def get_type(self) -> ValveType:
        """Get the type of the valve."""
        return self.valve_type

    def __repr__(self) -> str:
        return f"{self.pin}[{self.value}]"


class PneumaticNoValve(BaseValve):
    """
    This class represents a pneumatic valve. It is useful for testing purposes.
    It can also be used as a base class for other switchable devices.
    """

    def __init__(self, pin: int, name: str, gpio_pin: RPi, board: Board):
        super().__init__(pin, name, gpio_pin, board, ValveType.NORMALLY_CLOSED)


class Pump(BaseSwitch):
    """
    This class represents a pump. It is useful for testing purposes.
    It can also be used as a base class for other switchable devices.
    """

    def set(self, state: bool):
        super().set(state)
        if state:
            logging.info("Starting pump %s on pin %s", self.name, self.name)
        else:
            logging.info("Stopping pump %s on pin %s", self.name, self.name)

    def on(self):  # pylint: disable=invalid-name
        """Start the pump."""
        self.set(True)

    def off(self):
        """Stop the pump."""
        self.set(False)


def toggle(switch: Switchable):
    """
    Toggle the state of a switchable device.

    :param switch: The device to be toggled
    """
    switch.set(not switch.value)
    logging.debug("Toggled the switch: %s", switch)


def periodic_toggle(switch: Switchable, interval: float, loop_forever: bool = True, count: int = 0):
    """
    Periodically toggle the state of a switchable device.

    :param switch: The device to be toggled
    :param interval: The time interval between toggles in seconds
    :param loop_forever: If True, toggles the device indefinitely, else toggles it for 'count' times
    :param count: The number of times to toggle the device (ignored if loop_forever is True)
    """
    assert interval > 0, "Interval must be greater than 0"
    assert count > 0 or loop_forever, "Must toggle at least once"

    try:
        while loop_forever or count > 0:
            count -= 1 if count > 0 else 0
            toggle(switch)
            logging.debug(switch)
            time.sleep(interval)
    except SwitchingError as error:
        logging.error(error)
