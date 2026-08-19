"""
behavior.py

The personality state machine: HOST (sinister, smooth) <-> TRICKSTER
(mischievous, exaggerated). All hardware modules are injected into
`BehaviorManager` rather than constructed internally, so the manager is
easy to unit test with mocks and doesn't need to know how any given
peripheral is wired.

Knock and proximity sensors are small enough that they're defined here
alongside the state machine that consumes them, rather than as separate
top-level modules (the spec's module list doesn't include a dedicated
sensors.py) — each still follows the same real/mock backend pattern as
the other hardware modules.

Guest recognition: `BehaviorManager` does not know anything about
`script_lines.py` or how personalized dialogue is structured — it only
knows a guest was identified (via `vision.TrackingResult.identified_guest`)
and calls an injected `on_guest_recognized(guest_key)` callback, subject to
the confidence threshold and cooldown in `CONFIG.recognition`. This keeps
the dialogue-content/hardware-behavior separation intact: `main.py` is
responsible for deciding what a recognized guest key actually triggers.
"""

from __future__ import annotations

import logging
import time
from enum import Enum, auto
from typing import Callable, Protocol

from audio import AudioInput, AudioOutput
from config import CONFIG
from led import EyeColor, EyeController
from servo import ServoController
from vision import FaceTracker, TrackingResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Knock sensor
# ---------------------------------------------------------------------------

class KnockSensorBackend(Protocol):
    def was_knocked(self) -> bool:
        """Return True (and clear internal state) if a knock was detected
        since the last call. Non-blocking."""
        ...


class GPIOKnockSensorBackend:
    """Real hardware backend: a piezo/vibration sensor on a digital GPIO pin."""

    def __init__(self) -> None:
        from gpiozero import Button  # type: ignore

        self._button = Button(CONFIG.pins.knock_sensor, pull_up=True)
        self._flag = False
        self._button.when_pressed = self._on_press

    def _on_press(self) -> None:
        self._flag = True

    def was_knocked(self) -> bool:
        if self._flag:
            self._flag = False
            return True
        return False


class MockKnockSensorBackend:
    """Never fires on its own; useful for the automated test harness, which
    can flip `.simulate_knock()` to exercise the trigger path."""

    def __init__(self) -> None:
        self._flag = False

    def simulate_knock(self) -> None:
        self._flag = True

    def was_knocked(self) -> bool:
        if self._flag:
            self._flag = False
            return True
        return False


def _detect_knock_backend() -> KnockSensorBackend:
    try:
        return GPIOKnockSensorBackend()
    except Exception as exc:  # noqa: BLE001
        logger.info("GPIO knock sensor unavailable (%s); using mock.", exc)
        return MockKnockSensorBackend()


# ---------------------------------------------------------------------------
# Proximity sensor
# ---------------------------------------------------------------------------

class ProximitySensorBackend(Protocol):
    def distance_ft(self) -> float:
        """Return the current measured distance in feet."""
        ...


class GPIOProximitySensorBackend:
    """Real hardware backend for an HC-SR04 ultrasonic sensor."""

    def __init__(self) -> None:
        from gpiozero import DistanceSensor  # type: ignore

        self._sensor = DistanceSensor(
            echo=CONFIG.pins.proximity_echo,
            trigger=CONFIG.pins.proximity_trigger,
            max_distance=4.0,
        )

    def distance_ft(self) -> float:
        return self._sensor.distance * 3.28084  # meters -> feet


class MockProximitySensorBackend:
    """Reports a constant "far away" distance unless overridden for tests."""

    def __init__(self) -> None:
        self._distance_ft = 10.0

    def simulate_distance(self, feet: float) -> None:
        self._distance_ft = feet

    def distance_ft(self) -> float:
        return self._distance_ft


def _detect_proximity_backend() -> ProximitySensorBackend:
    try:
        return GPIOProximitySensorBackend()
    except Exception as exc:  # noqa: BLE001
        logger.info("GPIO proximity sensor unavailable (%s); using mock.", exc)
        return MockProximitySensorBackend()


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class Mode(Enum):
    HOST = auto()
    TRICKSTER = auto()


class BehaviorManager:
    """Drives the skeleton's personality state machine.

    All hardware-facing collaborators are injected via the constructor
    (dependency injection), so `BehaviorManager` has zero knowledge of
    GPIO pins, camera backends, etc. — it only calls the public interfaces
    of `FaceTracker`, `AudioInput`, `AudioOutput`, `ServoController`, and
    `EyeController`.
    """

    def __init__(
        self,
        vision: FaceTracker,
        audio_in: AudioInput,
        audio_out: AudioOutput,
        servos: ServoController,
        eyes: EyeController,
        knock_sensor: KnockSensorBackend | None = None,
        proximity_sensor: ProximitySensorBackend | None = None,
        on_guest_recognized: Callable[[str], None] | None = None,
    ) -> None:
        self._vision = vision
        self._audio_in = audio_in
        self._audio_out = audio_out
        self._servos = servos
        self._eyes = eyes
        self._knock = knock_sensor or _detect_knock_backend()
        self._proximity = proximity_sensor or _detect_proximity_backend()
        self._on_guest_recognized = on_guest_recognized

        self._mode = Mode.HOST
        self._last_trigger_time = time.monotonic()
        self._last_mode_switch_time = 0.0
        self._last_recognized_guest: str | None = None
        self._last_recognition_time = 0.0
        self._eyes.set_color(EyeColor.AMBER)
        self._eyes.enable_flicker(False)

    @property
    def mode(self) -> Mode:
        return self._mode

    # -- mode switching -----------------------------------------------------

    def _switch_to(self, mode: Mode) -> None:
        if mode == self._mode:
            return
        now = time.monotonic()
        if now - self._last_mode_switch_time < CONFIG.timing.mode_switch_cooldown_s:
            return  # cooldown active; ignore rapid re-triggering
        self._mode = mode
        self._last_mode_switch_time = now
        self._last_trigger_time = now
        if mode == Mode.TRICKSTER:
            self._eyes.set_color(EyeColor.RED)
            self._eyes.enable_flicker(True)
            logger.info("Mode -> TRICKSTER")
        else:
            self._eyes.set_color(EyeColor.AMBER)
            self._eyes.enable_flicker(False)
            logger.info("Mode -> HOST")

    def _check_triggers(self) -> None:
        """Poll all Trickster-mode triggers: loud noise, knock, proximity."""
        triggered = False

        if self._audio_in.consume_loud_event():
            triggered = True
            logger.debug("Trigger: loud noise")

        if self._knock.was_knocked():
            triggered = True
            logger.debug("Trigger: knock")

        if self._proximity.distance_ft() < CONFIG.proximity.trigger_distance_ft:
            triggered = True
            logger.debug("Trigger: proximity")

        if triggered:
            self._last_trigger_time = time.monotonic()
            self._switch_to(Mode.TRICKSTER)
        elif self._mode == Mode.TRICKSTER:
            elapsed = time.monotonic() - self._last_trigger_time
            if elapsed >= CONFIG.timing.trickster_timeout_s:
                self._switch_to(Mode.HOST)

    # -- guest recognition ----------------------------------------------------

    def _handle_recognition(self, tracking: TrackingResult) -> None:
        """Fire `on_guest_recognized` for a newly identified guest.

        Applies `CONFIG.recognition.confidence_threshold` (LBPH: lower
        confidence value = better match) and
        `CONFIG.recognition.cooldown_seconds` so a guest lingering in
        frame doesn't re-trigger the callback every tick. Dialogue content
        itself is intentionally not this module's concern — see the
        module docstring.
        """
        if tracking.identified_guest is None or tracking.recognition_confidence is None:
            return
        if tracking.recognition_confidence > CONFIG.recognition.confidence_threshold:
            return  # LBPH distance too high to trust as a match

        now = time.monotonic()
        same_guest = tracking.identified_guest == self._last_recognized_guest
        cooldown_elapsed = (
            now - self._last_recognition_time
        ) >= CONFIG.recognition.cooldown_seconds
        if same_guest and not cooldown_elapsed:
            return

        self._last_recognized_guest = tracking.identified_guest
        self._last_recognition_time = now
        logger.info(
            "Recognized guest: %s (confidence %.1f)",
            tracking.identified_guest,
            tracking.recognition_confidence,
        )
        if self._on_guest_recognized is not None:
            self._on_guest_recognized(tracking.identified_guest)

    # -- per-tick update ------------------------------------------------------

    def tick(self) -> None:
        """Advance the state machine and all hardware by one control-loop tick."""
        self._check_triggers()

        smoothing = (
            CONFIG.vision.tracking_smoothing_trickster
            if self._mode == Mode.TRICKSTER
            else CONFIG.vision.tracking_smoothing_host
        )
        easing = (
            CONFIG.servo.easing_factor_trickster
            if self._mode == Mode.TRICKSTER
            else CONFIG.servo.easing_factor_host
        )

        tracking = self._vision.read(smoothing)
        if tracking.face_found:
            target_pan = self._vision.offset_to_head_angle(tracking.horizontal_offset)
            target_tilt = self._vision.offset_to_tilt_angle(tracking.vertical_offset)
            self._servos.update_head(target_pan, easing)
            self._servos.update_tilt(target_tilt, easing)
            self._eyes.set_base_brightness(0.3 + 0.7 * tracking.closeness)
            self._handle_recognition(tracking)
        else:
            self._servos.center_head(easing * 0.5)
            self._servos.center_tilt(easing * 0.5)
            self._eyes.set_base_brightness(0.4)

        jaw_target = self._audio_in.amplitude_to_jaw_angle(self._audio_in.latest_rms)
        self._servos.update_jaw(jaw_target)

        self._eyes.tick()

    def maybe_speak(self, probability: float = 0.02) -> None:
        """Randomly queue a line appropriate to the current mode.

        Call once per tick from `main.py`; `probability` controls how often
        the skeleton spontaneously speaks (kept low to avoid audio spam).
        Uses TTS ~30% of the time and pre-recorded lines otherwise, per the
        hybrid audio requirement.
        """
        import random

        if random.random() >= probability:
            return
        mode_key = "trickster" if self._mode == Mode.TRICKSTER else "host"
        if random.random() < 0.3:
            self._audio_out.speak_random_tts(mode_key)
        else:
            self._audio_out.play_random_line(mode_key)
