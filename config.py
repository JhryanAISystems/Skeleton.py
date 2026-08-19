"""
config.py

Central configuration for the animatronic skeleton system, tuned for
Raspberry Pi Zero 2 W.

HARDWARE ASSUMPTIONS (Pi Zero 2 W specific)
---------------------------------------------
- Raspberry Pi Zero 2 W: quad-core Cortex-A53 @ 1GHz, 512MB RAM. This is
  enough for real-time Haar-cascade face detection at LOW resolution
  (320x240), but NOT enough for full-res (640x480+) detection at a smooth
  frame rate the way a Pi 4/5 could handle. This file's `VisionConfig`
  reflects that: smaller frame size, and `vision.py` is written to skip
  every other frame under load. If you swap to a Pi 4/5 later, bump
  `frame_width`/`frame_height` back up and remove the frame-skip.
- Camera: any Raspberry Pi Camera Module (v2, v3, or the older v1) BUT the
  Zero 2 W's CSI connector is the small/narrow style — you need a
  "Raspberry Pi Zero camera cable" adapter, not the standard-width ribbon
  that ships with the camera. This is the #1 thing first-timers get wrong
  ordering parts for this build.
- The Zero 2 W has NO built-in audio jack and NO full-size USB port. Mic
  and speaker are handled via a single USB audio adapter (mic-in +
  headphone-out combo dongle) plugged into a micro-USB OTG adapter on the
  Zero's data-capable micro-USB port (the one labeled "USB", not "PWR").
- Two MG996R servos (head pan, jaw) via PWM through `gpiozero`.
- Amber/red-capable eye LEDs, PWM-driven via `gpiozero.PWMLED`.
- Knock sensor (piezo/vibration) on a GPIO input pin.
- HC-SR04 ultrasonic proximity sensor for the "close proximity" trigger.
- GPIO pin numbers below use BCM numbering and match the standard 40-pin
  header, which the Zero 2 W shares with every other modern Pi — so if you
  later upgrade to a Pi 4/5, your wiring and these pin numbers don't change.
- Control loop target: ~15 Hz (slower than a Pi 4's ~25 Hz) to leave the
  Zero 2 W's CPU headroom for face detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class GPIOPins:
    """BCM pin assignments for all hardware peripherals."""

    head_servo: int = 17
    jaw_servo: int = 27
    eye_led_left: int = 22
    eye_led_right: int = 23
    knock_sensor: int = 24
    proximity_trigger: int = 5   # HC-SR04 TRIG
    proximity_echo: int = 6      # HC-SR04 ECHO


@dataclass(frozen=True)
class ServoLimits:
    """Angle limits and easing behavior for each servo, in degrees."""

    head_min_deg: float = 30.0
    head_center_deg: float = 90.0
    head_max_deg: float = 150.0

    jaw_closed_deg: float = 20.0
    jaw_open_deg: float = 70.0

    easing_factor_host: float = 0.12
    easing_factor_trickster: float = 0.35


@dataclass(frozen=True)
class AudioConfig:
    """Microphone thresholds and jaw-mapping parameters.

    Read via a USB audio adapter (mic-in), not I2S — much simpler to set
    up on a Zero 2 W than wiring a raw I2S mic and fighting ALSA overlays.
    """

    sample_rate_hz: int = 16000
    block_size: int = 512
    input_channels: int = 1

    ambient_noise_floor: float = 0.02
    loud_noise_threshold: float = 0.55

    jaw_map_min_amplitude: float = 0.03
    jaw_map_max_amplitude: float = 0.45


@dataclass(frozen=True)
class VisionConfig:
    """Face-tracking sensitivity and smoothing parameters.

    Frame size is intentionally small (320x240) — the Zero 2 W's CPU can't
    sustain Haar-cascade detection on larger frames without the control
    loop stuttering. `vision.py` also skips detection on alternating
    frames to keep the rest of the loop (servo/LED/audio) responsive.
    """

    frame_width: int = 320
    frame_height: int = 240
    detection_scale_factor: float = 1.2
    detection_min_neighbors: int = 4
    # Run face detection on 1 out of every N captured frames; the servo
    # target simply holds steady between detections thanks to easing.
    detect_every_n_frames: int = 2

    tracking_smoothing_host: float = 0.15
    tracking_smoothing_trickster: float = 0.45

    close_face_bbox_height_px: int = 140  # scaled down for the 320x240 frame


@dataclass(frozen=True)
class ProximityConfig:
    """Ultrasonic proximity sensor thresholds."""

    trigger_distance_ft: float = 2.0
    poll_interval_s: float = 0.15


@dataclass(frozen=True)
class TimingConfig:
    """Mode-switching and timeout behavior."""

    trickster_timeout_s: float = 20.0
    mode_switch_cooldown_s: float = 4.0
    # Slower than a Pi 4/5 build (25 Hz) to leave CPU room for face detection.
    loop_hz: float = 15.0


@dataclass(frozen=True)
class AudioLineConfig:
    """File paths and example line sets for each personality mode."""

    audio_dir: Path = Path("assets/audio")

    host_prerecorded: tuple[str, ...] = (
        "host_greeting_01.wav",
        "host_greeting_02.wav",
        "host_idle_murmur.wav",
    )
    trickster_prerecorded: tuple[str, ...] = (
        "trickster_laugh_01.wav",
        "trickster_jumpscare_01.wav",
        "trickster_taunt_01.wav",
    )

    host_tts_lines: tuple[str, ...] = (
        "Welcome... if you dare.",
        "I've been expecting you.",
        "Do come closer, won't you?",
    )
    trickster_tts_lines: tuple[str, ...] = (
        "Boo! Did I get you?",
        "Oh, you jumped! Hehehe.",
        "Knock knock. Who's there? ME.",
    )

    tts_voice_rate_wpm: int = 165
    tts_voice_id: str | None = None


@dataclass(frozen=True)
class SystemConfig:
    """Top-level container bundling all sub-configs."""

    pins: GPIOPins = field(default_factory=GPIOPins)
    servo: ServoLimits = field(default_factory=ServoLimits)
    audio: AudioConfig = field(default_factory=AudioConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    proximity: ProximityConfig = field(default_factory=ProximityConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    lines: AudioLineConfig = field(default_factory=AudioLineConfig)


CONFIG = SystemConfig()
