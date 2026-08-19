"""
led.py

PWM-driven eye LED control: brightness scaling, flicker effects, and
Host (amber) / Trickster (red) color switching.

Hardware assumption: each eye is a single PWM-capable LED channel (or an
amber/red bi-color LED where only one color is lit at a time). If you're
using true RGB LEDs, extend `EyeController` to drive R/G/B channels
independently instead of a single brightness value.
"""

from __future__ import annotations

import logging
import random
from enum import Enum, auto
from typing import Protocol

from config import CONFIG

logger = logging.getLogger(__name__)


class EyeColor(Enum):
    """Supported eye color states."""

    AMBER = auto()
    RED = auto()


class LEDBackend(Protocol):
    """Hardware abstraction for a single PWM LED channel."""

    def set_brightness(self, pin: int, value: float) -> None:
        """Set brightness in [0.0, 1.0] on `pin`."""
        ...

    def close(self) -> None:
        ...


class MockLEDBackend:
    """Logs brightness changes instead of driving real hardware."""

    def set_brightness(self, pin: int, value: float) -> None:
        logger.debug("MOCK LED pin=%d -> %.2f", pin, value)

    def close(self) -> None:
        logger.debug("MOCK LED backend closed")


class GPIOLEDBackend:
    """Real hardware backend using gpiozero.PWMLED."""

    def __init__(self) -> None:
        from gpiozero import PWMLED  # type: ignore

        self._PWMLED = PWMLED
        self._leds: dict[int, "PWMLED"] = {}

    def _get_led(self, pin: int):
        if pin not in self._leds:
            self._leds[pin] = self._PWMLED(pin)
        return self._leds[pin]

    def set_brightness(self, pin: int, value: float) -> None:
        led = self._get_led(pin)
        led.value = max(0.0, min(1.0, value))

    def close(self) -> None:
        for led in self._leds.values():
            led.close()
        self._leds.clear()


def _detect_backend() -> LEDBackend:
    try:
        return GPIOLEDBackend()
    except Exception as exc:  # noqa: BLE001
        logger.info("GPIO LED backend unavailable (%s); using mock.", exc)
        return MockLEDBackend()


class EyeController:
    """Controls both eye LEDs: base brightness, flicker, and color."""

    def __init__(self, backend: LEDBackend | None = None) -> None:
        self._backend = backend or _detect_backend()
        self._color = EyeColor.AMBER
        self._base_brightness = 0.6
        self._flicker_enabled = False

    @property
    def color(self) -> EyeColor:
        return self._color

    def set_color(self, color: EyeColor) -> None:
        """Switch eye color (e.g., amber for Host, red for Trickster).

        Note: with single-channel PWM LEDs this is a logical state used by
        calling code to choose which physical LED (amber vs red) to drive.
        For true bi-color LEDs, wire both colors to separate pins and pick
        the active pin based on `self._color` inside `apply_brightness`.
        """
        self._color = color
        logger.debug("Eye color set to %s", color.name)

    def set_base_brightness(self, value: float) -> None:
        """Set the steady-state brightness in [0.0, 1.0].

        Typically driven by `vision.FaceTracker` distance estimation: closer
        faces -> brighter eyes.
        """
        self._base_brightness = max(0.0, min(1.0, value))

    def enable_flicker(self, enabled: bool) -> None:
        """Toggle randomized flicker on top of the base brightness."""
        self._flicker_enabled = enabled

    def tick(self) -> None:
        """Compute and push one frame of brightness to both eyes.

        Call this once per main-loop iteration.
        """
        brightness = self._base_brightness
        if self._flicker_enabled:
            # Randomized flicker: subtract a random dip, occasionally a
            # sharper "candle flicker" dropout.
            dip = random.uniform(0.0, 0.25)
            if random.random() < 0.08:
                dip += random.uniform(0.2, 0.4)
            brightness = max(0.05, brightness - dip)

        self._backend.set_brightness(CONFIG.pins.eye_led_left, brightness)
        self._backend.set_brightness(CONFIG.pins.eye_led_right, brightness)

    def shutdown(self) -> None:
        self._backend.close()
