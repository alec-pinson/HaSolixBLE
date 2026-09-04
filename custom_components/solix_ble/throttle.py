"""Update throttling for sensor entities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from SolixBLE import SolixBLEDevice

_LOGGER = logging.getLogger(__name__)


class SolixThrottle:
    """Rate limits device state notifications on their way to entities.

    Registers a single callback with the device and fans out to its own
    subscribers at most once per interval.
    """

    def __init__(
        self, hass: HomeAssistant, device: SolixBLEDevice, interval: float
    ) -> None:
        """Initialize the throttle and subscribe to the device."""

        self._hass = hass
        self._device = device
        self._interval = interval
        self._callbacks: list[Callable[[], None]] = []

        device.add_callback(self._device_updated)

    def add_callback(self, callback: Callable[[], None]) -> None:
        """Register a subscriber to be run on a throttled update."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """De-register a subscriber."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _device_updated(self) -> None:
        """Run when the device reports a state change."""
        self._fan_out()

    def _fan_out(self) -> None:
        """Run every registered subscriber."""
        for callback in self._callbacks:
            try:
                callback()
            except Exception:
                _LOGGER.exception(
                    f"Exception raised by a throttled state change callback '{callback}'!"
                )
