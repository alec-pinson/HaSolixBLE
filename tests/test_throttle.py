"""Test the update throttle for the SolixBLE integration."""

from datetime import timedelta
from unittest.mock import MagicMock

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_fire_time_changed

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


async def test_first_update_fans_out_immediately(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The first update after construction is published straight away."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)

    assert callback.call_count == 1


async def test_updates_inside_window_are_suppressed(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Updates arriving inside the window do not reach subscribers."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    freezer.tick(timedelta(seconds=1))
    fire(device)
    freezer.tick(timedelta(seconds=7))
    fire(device)

    assert callback.call_count == 1


async def test_held_update_is_flushed_when_window_closes(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The most recent suppressed update is published at the end of the window."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    freezer.tick(timedelta(seconds=1))
    fire(device)

    assert callback.call_count == 1

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert callback.call_count == 2


async def test_no_flush_when_nothing_was_held(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A window that suppressed nothing does not publish at its end."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert callback.call_count == 1


async def test_update_after_window_fans_out_immediately(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """An update arriving after the window has elapsed is published at once."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    freezer.tick(timedelta(seconds=31))
    fire(device)

    assert callback.call_count == 2
