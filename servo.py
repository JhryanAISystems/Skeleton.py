"""
servo.py

Head-pan and jaw servo control, with software easing for smooth motion.

Hardware assumption: two MG996R servos driven via PWM. On a real Pi this
uses `gpiozero.AngularServo` (which itself typically rides on the `pigpio`
pin factory for jitter-free PWM). When `gpiozero`/GPIO hardware isn't
available (e.g., developing on a laptop), a `MockServoBackend` is used
instead so the rest of the system runs unmodified.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Protocol

from config import CONFIG

logger = logging.getLogger(__name__)


class ServoBackend(Protocol):
    """Hardware abstraction that any servo backend must implement."""

    def set_angle(self, pin: int, angle_deg: float) -> None:
        """Drive the servo on `pin` to `angle_deg` immediately (no easing)."""
        ...

    def close(self) -> None:
        """Release hardware resources."""
        ...


class MockServoBackend:
    """Logs servo commands instead of driving real hardware.

    Auto-selected on any machine without `gpiozero` + GPIO access, so the
    full behavior/vision/audio stack can be developed and tested off-Pi.
    """

    def __init__(self) -> None:
        self._last_angles: dict[int, float] = {}

    def set_angle(self, pin: int, angle_deg: float) -> None:
        self._last_angles[pin] = angle_deg
        logger.debug("MOCK servo pin=%d -> %.1f deg", pin, angle_deg)

    def close(self) -> None:
        logger.debug("MOCK servo backend closed")


class GPIOServoBackend:
    """Real hardware backend using gpiozero.AngularServo.

    Only imports `gpiozero` at construction time so environments without
    the library (or without GPIO access) never fail at module import.
    """

    def __init__(self) -> None:
        from gpiozero import AngularServo  # type: ignore  # local import

        self._AngularServo = AngularServo
        self._servos: dict[int, "AngularServo"] = {}

    def _get_servo(self, pin: int):
        if pin not in self._servos:
            self._servos[pin] = self._AngularServo(
                pin,
                min_angle=0,
                max_angle=180,
                min_pulse_width=0.0005,
                max_pulse_width=0.0025,
            )
        return self._servos[pin]

    def set_angle(self, pin: int, angle_deg: float) -> None:
        servo = self._get_servo(pin)
        servo.angle = max(0.0, min(180.0, angle_deg))

    def close(self) -> None:
        for servo in self._servos.values():
            servo.close()
        self._servos.clear()


def _detect_backend() -> ServoBackend:
    """Return a real GPIO backend if available, else fall back to mock."""
    try:
        return GPIOServoBackend()
    except Exception as exc:  # noqa: BLE001 - broad by design for hw fallback
        logger.info("GPIO servo backend unavailable (%s); using mock.", exc)
        return MockServoBackend()


def ease_toward(current: float, target: float, factor: float) -> float:
    """Move `current` a fraction (`factor`) of the way toward `target`.

    This is a simple exponential ease: each tick covers `factor` of the
    remaining distance, producing smooth deceleration as the target is
    approached. `factor` should be in (0.0, 1.0].
    """
    factor = max(0.0, min(1.0, factor))
    return current + (target - current) * factor


class ServoController:
    """Owns the head-pan and jaw servos and exposes eased movement."""

    def __init__(self, backend: ServoBackend | None = None) -> None:
        self._backend = backend or _detect_backend()
        self._head_angle = CONFIG.servo.head_center_deg
        self._jaw_angle = CONFIG.servo.jaw_closed_deg
        # Push initial positions to hardware.
        self._backend.set_angle(CONFIG.pins.head_servo, self._head_angle)
        self._backend.set_angle(CONFIG.pins.jaw_servo, self._jaw_angle)

    @property
    def head_angle(self) -> float:
        """Current (eased) head servo angle in degrees."""
        return self._head_angle

    @property
    def jaw_angle(self) -> float:
        """Current (eased) jaw servo angle in degrees."""
        return self._jaw_angle

    def update_head(self, target_deg: float, easing_factor: float) -> None:
        """Ease the head servo one tick toward `target_deg`."""
        clamped = max(
            CONFIG.servo.head_min_deg, min(CONFIG.servo.head_max_deg, target_deg)
        )
        self._head_angle = ease_toward(self._head_angle, clamped, easing_factor)
        self._backend.set_angle(CONFIG.pins.head_servo, self._head_angle)

    def update_jaw(self, target_deg: float, easing_factor: float = 0.5) -> None:
        """Ease the jaw servo one tick toward `target_deg`."""
        clamped = max(
            CONFIG.servo.jaw_closed_deg,
            min(CONFIG.servo.jaw_open_deg, target_deg),
        )
        self._jaw_angle = ease_toward(self._jaw_angle, clamped, easing_factor)
        self._backend.set_angle(CONFIG.pins.jaw_servo, self._jaw_angle)

    def center_head(self, easing_factor: float) -> None:
        """Ease the head back toward its center resting position."""
        self.update_head(CONFIG.servo.head_center_deg, easing_factor)

    def close_jaw(self, easing_factor: float = 0.5) -> None:
        """Ease the jaw toward fully closed."""
        self.update_jaw(CONFIG.servo.jaw_closed_deg, easing_factor)

    def shutdown(self) -> None:
        """Release hardware resources."""
        self._backend.close()
