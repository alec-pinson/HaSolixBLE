"""Test the update throttle for the SolixBLE integration."""

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

from custom_components.solix_ble.throttle import SolixThrottle


def make_device() -> MagicMock:
    """Build a mock device that records its registered callback."""
    device = MagicMock()
    device.available = True
    device.add_callback = MagicMock()
    device.remove_callback = MagicMock()
    return device


def fire(device: MagicMock) -> None:
    """Invoke the callback the throttle registered with the device."""
    device.add_callback.call_args[0][0]()


async def test_registers_one_callback_with_device(hass: HomeAssistant) -> None:
    """The throttle subscribes to the device exactly once."""
    device = make_device()

    SolixThrottle(hass, device, 0)

    assert device.add_callback.call_count == 1


async def test_disabled_passes_every_update_through(hass: HomeAssistant) -> None:
    """An interval of zero fans out on every device update."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 0)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    fire(device)
    fire(device)

    assert callback.call_count == 3


async def test_removed_callback_is_not_called(hass: HomeAssistant) -> None:
    """A de-registered subscriber stops receiving updates."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 0)
    callback = MagicMock()
    throttle.add_callback(callback)
    throttle.remove_callback(callback)

    fire(device)

    assert callback.call_count == 0
