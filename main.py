"""
main.py

Entry point for the animatronic skeleton system. Initializes all hardware
modules (real backends on a Pi, mock backends elsewhere), wires them into
`BehaviorManager` via dependency injection, and runs the main control loop.

Usage:
    python main.py            # run the live control loop
    python main.py --test     # run a short simulated session on mock hardware
"""

from __future__ import annotations

import argparse
import logging
import random
import time

from audio import AudioInput, AudioOutput
from behavior import BehaviorManager, Mode, MockKnockSensorBackend, MockProximitySensorBackend
from config import CONFIG
from led import EyeController
from servo import ServoController
from vision import FaceTracker

logger = logging.getLogger(__name__)


def make_guest_greeting_callback(audio_out: AudioOutput):
    """Build the `on_guest_recognized` callback passed to `BehaviorManager`.

    This is the one place that bridges recognition (guest key, generic)
    to actual dialogue content (`script_lines.py`, personal/private —
    not tracked in this repo, see .gitignore). Import is deferred and
    wrapped so the system degrades gracefully if `script_lines.py` isn't
    present on this machine (e.g. a fresh clone before it's been copied
    over separately, per BUILD_GUIDE.md).

    NOTE: this assumes `script_lines.py` exposes a `GUESTS` dict shaped
    roughly like:
        GUESTS = {
            "guest_key": {
                "display_name": "...",
                "lines": [{"text": "..."}, ...],
            },
            ...
        }
    Adjust the lookup below if your actual structure differs.
    """

    def _on_guest_recognized(guest_key: str) -> None:
        try:
            from script_lines import GUESTS  # type: ignore
        except ImportError:
            logger.debug(
                "script_lines.py not found; skipping personalized greeting "
                "for guest '%s'", guest_key,
            )
            return

        guest = GUESTS.get(guest_key)
        if not guest:
            logger.debug("Guest key '%s' not found in script_lines.GUESTS", guest_key)
            return

        lines = guest.get("lines") or []
        if not lines:
            return

        choice = random.choice(lines)
        text = choice.get("text") if isinstance(choice, dict) else str(choice)
        if text:
            audio_out.speak_text(text)

    return _on_guest_recognized


def build_behavior_manager() -> BehaviorManager:
    """Construct all hardware modules and inject them into a BehaviorManager.

    Each module auto-detects real vs. mock hardware internally, so this
    function works unmodified both on a Raspberry Pi and on a dev laptop.
    """
    vision = FaceTracker()
    audio_in = AudioInput()
    audio_out = AudioOutput()
    servos = ServoController()
    eyes = EyeController()

    return BehaviorManager(
        vision=vision,
        audio_in=audio_in,
        audio_out=audio_out,
        servos=servos,
        eyes=eyes,
        on_guest_recognized=make_guest_greeting_callback(audio_out),
    )


def run_main_loop(manager: BehaviorManager) -> None:
    """Run the non-blocking control loop at the configured tick rate.

    The loop itself contains no blocking calls: vision reads a single
    already-captured frame, audio amplitude is read from a background
    thread's latest value, and audio playback/TTS are queued onto a
    separate worker thread. Only a short `time.sleep` is used to hold the
    loop to its target rate, which is standard practice for a fixed-tick
    control loop (as opposed to blocking on I/O).
    """
    tick_period = 1.0 / CONFIG.timing.loop_hz
    logger.info("Starting main control loop at %.1f Hz", CONFIG.timing.loop_hz)

    try:
        while True:
            loop_start = time.monotonic()

            manager.tick()
            manager.maybe_speak()

            elapsed = time.monotonic() - loop_start
            sleep_time = max(0.0, tick_period - elapsed)
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        logger.info("Shutdown requested (Ctrl+C).")


def run_test_harness() -> None:
    """Lightweight inline smoke test using fully mocked hardware.

    Verifies:
      1. The system initializes without error (including the new tilt
         servo and recognizer backend detection).
      2. A knock event correctly triggers a switch to TRICKSTER mode.
      3. A number of ticks run cleanly without exceptions in TRICKSTER mode.
      4. Mode reverts to HOST once the trickster timeout window would have
         elapsed (simulated by directly manipulating the manager's timer).

    This is intentionally lightweight rather than a full pytest suite, per
    the project spec's request for "a simple test harness in main.py".
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("=== Running test harness (mock hardware) ===")

    vision = FaceTracker()
    audio_in = AudioInput()
    audio_out = AudioOutput()
    servos = ServoController()
    eyes = EyeController()
    knock = MockKnockSensorBackend()
    proximity = MockProximitySensorBackend()

    manager = BehaviorManager(
        vision=vision,
        audio_in=audio_in,
        audio_out=audio_out,
        servos=servos,
        eyes=eyes,
        knock_sensor=knock,
        proximity_sensor=proximity,
        on_guest_recognized=make_guest_greeting_callback(audio_out),
    )

    assert manager.mode == Mode.HOST, "Should start in HOST mode"
    logger.info("PASS: initial mode is HOST")

    for _ in range(5):
        manager.tick()
    logger.info("PASS: ticks run cleanly with pan/tilt + recognition wired in")

    knock.simulate_knock()
    manager.tick()
    assert manager.mode == Mode.TRICKSTER, "Knock should trigger TRICKSTER mode"
    logger.info("PASS: knock event switched mode to TRICKSTER")

    for _ in range(10):
        manager.tick()
    assert manager.mode == Mode.TRICKSTER, "Should remain TRICKSTER before timeout"
    logger.info("PASS: mode remains TRICKSTER before timeout elapses")

    # Simulate timeout elapsing without touching private state directly
    # from outside the class in production code -- acceptable here since
    # this is a same-module test harness exercising internal behavior.
    manager._last_trigger_time -= CONFIG.timing.trickster_timeout_s + 1.0  # noqa: SLF001
    manager._last_mode_switch_time = 0.0  # noqa: SLF001
    manager.tick()
    assert manager.mode == Mode.HOST, "Mode should revert to HOST after timeout"
    logger.info("PASS: mode reverted to HOST after timeout")

    servos.shutdown()
    eyes.shutdown()
    audio_in.shutdown()
    audio_out.shutdown()
    vision.close()

    logger.info("=== All test harness checks passed ===")


def main() -> None:
    parser = argparse.ArgumentParser(description="Animatronic skeleton control system")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a short simulated session on mock hardware and exit.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.test:
        run_test_harness()
        return

    manager = build_behavior_manager()
    run_main_loop(manager)


if __name__ == "__main__":
    main()
