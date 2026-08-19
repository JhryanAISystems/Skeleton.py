# Skeletonpy

Control software for an animatronic Halloween skeleton running on a Raspberry
Pi 4 Model B (4GB). It tracks faces with a camera, syncs the jaw to microphone
volume, switches between a calm "Host" and a jump-scare "Trickster"
personality, and speaks via pre-recorded lines and offline text-to-speech.

For the physical build (parts list, wiring, 3D-printed mounts, OS setup),
see [BUILD_GUIDE.md](BUILD_GUIDE.md). This README covers the software.

> **Note on hardware history:** this project originally targeted the
> Raspberry Pi Zero 2 W. Due to a prolonged supply shortage, the board was
> switched to a Pi 4 Model B (4GB). The Pi 4's larger footprint means it no
> longer fits inside the skull — it now lives in a separate torso/ribcage
> enclosure, connected to the skull's camera, servos, and LEDs by extended
> cables. The software stack is unchanged by this swap.

## How it works

`main.py` builds all hardware modules and wires them into a single
`BehaviorManager`, then runs a non-blocking control loop at
`CONFIG.timing.loop_hz` (~15 Hz):

1. `BehaviorManager.tick()` — polls triggers, updates head/jaw servo targets
   from vision/audio, and advances eye brightness.
2. `BehaviorManager.maybe_speak()` — occasionally queues a spoken line.

Every hardware-facing module (camera, mic/speaker, servos, LEDs, knock and
proximity sensors) follows the same pattern: a real backend using the actual
library (`picamera2`, `sounddevice`, `gpiozero`, ...), and a mock backend
that's auto-selected when the real one fails to import or initialize. This
means the exact same code runs on the Pi and on a dev laptop with no flags
or config changes.

### Personality state machine (`behavior.py`)

- **HOST** (default): amber, steady eyes; slower tracking/servo easing.
- **TRICKSTER**: red, flickering eyes; snappier tracking/servo easing.
- Switches to TRICKSTER on a loud noise, a knock, or someone getting within
  `CONFIG.proximity.trigger_distance_ft`. Auto-reverts to HOST after
  `CONFIG.timing.trickster_timeout_s` of no new triggers. A cooldown
  (`CONFIG.timing.mode_switch_cooldown_s`) prevents rapid re-triggering.

## Key files

| File | Responsibility |
|---|---|
| [main.py](main.py) | Entry point; builds the `BehaviorManager` and runs the control loop or `--test` smoke test |
| [behavior.py](behavior.py) | HOST/TRICKSTER state machine; knock and proximity sensor backends |
| [vision.py](vision.py) | Camera capture + Haar-cascade face tracking → head angle & closeness |
| [servo.py](servo.py) | Head/jaw servo control with eased (smoothed) motion |
| [audio.py](audio.py) | Mic amplitude sensing (jaw sync, loud-noise trigger) + non-blocking playback/TTS |
| [led.py](led.py) | Eye LED brightness, flicker, and Host/Trickster color state |
| [config.py](config.py) | All tunable parameters: GPIO pins, servo limits, thresholds, timing, audio line sets |
| [script_lines.py](script_lines.py) | Spoken-line content (guest lines, event lines, monologues) — kept separate from `config.py`. **Not tracked in this repo** — contains personalized guest content, kept local-only. |
| [generate_audio.py](generate_audio.py) | One-time offline script (run on a dev machine, not the Pi) that batch-generates MP3s via the ElevenLabs API from `script_lines.py` |
| `*.scad` | OpenSCAD source for 3D-printed mounts (see `BUILD_GUIDE.md` Part 4) |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

On a dev machine without Pi hardware, only `opencv-python` and `numpy` are
strictly required to run — everything else falls back to a mock backend if
its library or hardware isn't available.

## Usage

```bash
python main.py --test              # mock-hardware smoke test, then exit
python main.py                     # live run (real hardware where available)
python main.py --log-level DEBUG   # verbose logging
```

To (re)generate spoken-line audio from `script_lines.py`:

```bash
pip install requests
setx ELEVENLABS_API_KEY "your-key-here"   # Windows; reopen the shell after
python generate_audio.py
```

This writes MP3s into `audio/`, resuming safely if interrupted (existing
files are skipped). Copy the resulting `audio/` folder onto the Pi —
`audio.py` only plays files by name, it does not call the API on-device.

## Configuration

All tunables live in [config.py](config.py) as frozen dataclasses grouped by
subsystem (`GPIOPins`, `ServoLimits`, `AudioConfig`, `VisionConfig`,
`ProximityConfig`, `TimingConfig`, `AudioLineConfig`), bundled under the
module-level `CONFIG` singleton. Defaults were originally tuned for the Pi
Zero 2 W's limited CPU (smaller camera frame, frame-skipped detection,
slower loop rate). On the Pi 4, these are conservative rather than
necessary — there's headroom to raise camera resolution or loop rate if
you want a snappier feel, but the defaults are left as-is since they
already work reliably.

## Gotchas

- `main.py --test` reports in its log output which backend (real or mock)
  was selected for each module — if something you've wired up shows "mock",
  that's the first thing to check. Note that on a non-Pi dev machine (e.g.
  Windows), `picamera2` and `gpiozero` are *expected* to fall back to mock —
  that's the graceful-degradation design working as intended, not a bug.
- `generate_audio.py` is meant to run once, off-Pi, before deployment — not
  as part of the live control loop.
- Jittery head tracking or unreliable low-light detection are tuned via
  `tracking_smoothing_host` and `detection_min_neighbors` in `config.py`
  (see `BUILD_GUIDE.md` Part 5, steps 3 and 5).
- Since the Pi 4 lives in the torso rather than the skull, cable runs from
  skull to torso are longer than the original Pi Zero 2 W design assumed —
  see `BUILD_GUIDE.md` Part 2.8 for routing notes.
