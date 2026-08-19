"""
config.py

Central configuration for the animatronic skeleton system.

HARDWARE HISTORY
-----------------
Originally tuned for a Raspberry Pi Zero 2 W; a supply shortage forced a
pivot to a Raspberry Pi 4 Model B (4GB). The Pi 4 has considerably more
headroom, so the vision/timing defaults below (originally chosen to keep
the Zero 2 W's single-1GHz-quad-core CPU from stuttering) are left as
conservative-but-safe rather than strictly necessary. Bump
`frame_width`/`frame_height` or `loop_hz` up if you want a snappier feel;
nothing below requires it to work correctly on a Pi 4.

HARDWARE ASSUMPTIONS
---------------------------------------------
- Raspberry Pi 4 Model B (4GB). Lives in a torso/ribcage enclosure — it no
  longer fits inside the skull alongside the camera and servos, so those
  peripherals connect back to it via extended cables (see BUILD_GUIDE.md).
- Camera: Raspberry Pi Camera Module 3, using the standard CSI cable that
  ships with it (no narrow-CSI adapter needed on a Pi 4).
- Three MG996R servos: **pan** (`head_servo`, left/right), **tilt**
  (`tilt_servo`, up/down), and **jaw**. Pan and tilt are driven together
  each tick to track a detected face; jaw is driven independently from
  microphone amplitude.
- No built-in audio jack assumption removed — Pi 4 has one, but a USB
  audio adapter is still recommended for cleaner mic input; see
  `audio.py`.
- Amber/red-capable eye LEDs, PWM-driven via `gpiozero.PWMLED`.
- Knock sensor (piezo/vibration) on a GPIO input pin.
- HC-SR04 ultrasonic proximity sensor for the "close proximity" trigger.
- GPIO pin numbers below use BCM numbering and match the standard 40-pin
  header, unchanged across the Pi family.
- Control loop target: ~15 Hz. This was originally a Zero-2-W-conservative
  choice; the Pi 4 has room to run faster if desired.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class GPIOPins:
    """BCM pin assignments for all hardware peripherals."""

    head_servo: int = 17    # pan (left/right)
    tilt_servo: int = 26    # tilt (up/down)
    jaw_servo: int = 27
    eye_led_left: int = 22
    eye_led_right: int = 23
    knock_sensor: int = 24
    proximity_trigger: int = 5   # HC-SR04 TRIG
    proximity_echo: int = 6      # HC-SR04 ECHO


@dataclass(frozen=True)
class ServoLimits:
    """Angle limits and easing behavior for each servo, in degrees.

    Pan and tilt both use a modest range of motion from center — wide
    enough to look natural, narrow enough to keep the head looking
    intentional rather than a whipping full 180° sweep.
    """

    head_min_deg: float = 30.0     # pan
    head_center_deg: float = 90.0
    head_max_deg: float = 150.0

    tilt_min_deg: float = 60.0     # tilt: ~30° up/down from center
    tilt_center_deg: float = 90.0
    tilt_max_deg: float = 120.0

    jaw_closed_deg: float = 20.0
    jaw_open_deg: float = 70.0

    easing_factor_host: float = 0.12
    easing_factor_trickster: float = 0.35


@dataclass(frozen=True)
class AudioConfig:
    """Microphone thresholds and jaw-mapping parameters."""

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

    Frame size and frame-skip were originally chosen for the Zero 2 W's
    limited CPU. The Pi 4 has comfortable headroom to run these values as
    conservative defaults rather than hard requirements.
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
class RecognitionConfig:
    """Face recognition (LBPH) thresholds and behavior.

    LBPH confidence is a *distance*, not a typical ML confidence score —
    LOWER values mean a closer match. `confidence_threshold` is the
    maximum LBPH distance accepted as a positive identification. Usable
    range is usually roughly 40-90 depending on enrollment photo quality
    and lighting; this default is a conservative starting point to tune
    against your own enrolled guests (see `enroll_faces.py` /
    `train_recognizer.py`).

    If `model_path`/`label_map_path` don't exist, `vision.py` falls back
    to tracking-only mode automatically — recognition is treated as
    optional, not required for the prop to function.
    """

    confidence_threshold: float = 80.0
    cooldown_seconds: float = 8.0
    model_path: Path = Path("face_model.yml")
    label_map_path: Path = Path("label_map.json")
    face_sample_size: tuple[int, int] = (200, 200)


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
    recognition: RecognitionConfig = field(default_factory=RecognitionConfig)
    proximity: ProximityConfig = field(default_factory=ProximityConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    lines: AudioLineConfig = field(default_factory=AudioLineConfig)


CONFIG = SystemConfig()
