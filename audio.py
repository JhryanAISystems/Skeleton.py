"""
audio.py

Microphone amplitude sensing (for jaw sync + loud-noise detection) and
non-blocking audio output (pre-recorded lines + TTS).

Concurrency choice: threading (not asyncio) is used throughout this module.
Audio I/O here is dominated by blocking C-library calls (`sounddevice`
callbacks, file playback, TTS engine `runAndWait`), which don't offer async
equivalents. A background thread + queue is simpler and more robust for
this than wrapping blocking calls in an executor, and it keeps `main.py`'s
control loop fully synchronous and easy to reason about.

Hardware note: a single USB audio adapter (combo mic-in + headphone-out
dongle) is recommended for clean mic input, plugged in via USB. (The
original Pi Zero 2 W target had no built-in audio jack at all, requiring
a micro-USB OTG adapter for this; the Pi 4 has a full-size USB port and
its own 3.5mm jack, but a USB audio dongle is still the more reliable
choice for mic input.) `sounddevice` and the playback backends below
auto-detect the USB audio device as the default ALSA device — no special
config needed beyond `raspi-config`'s audio output selection (see the
Software Setup section in the build guide).
"""

from __future__ import annotations

import logging
import queue
import random
import threading
import time
from pathlib import Path
from typing import Protocol

import numpy as np

from config import CONFIG

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Amplitude input
# ---------------------------------------------------------------------------

class MicBackend(Protocol):
    """Hardware abstraction for a streaming microphone source."""

    def start(self, callback) -> None:
        """Begin streaming; `callback(rms: float)` is invoked per audio block."""
        ...

    def stop(self) -> None:
        ...


class SoundDeviceMicBackend:
    """Real hardware backend using the `sounddevice` library."""

    def __init__(self) -> None:
        import sounddevice as sd  # type: ignore

        self._sd = sd
        self._stream = None

    def start(self, callback) -> None:
        def _on_audio(indata, frames, time_info, status):  # noqa: ANN001
            if status:
                logger.debug("sounddevice status: %s", status)
            rms = float(np.sqrt(np.mean(np.square(indata))))
            callback(rms)

        self._stream = self._sd.InputStream(
            samplerate=CONFIG.audio.sample_rate_hz,
            blocksize=CONFIG.audio.block_size,
            channels=CONFIG.audio.input_channels,
            callback=_on_audio,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None


class MockMicBackend:
    """Generates synthetic ambient-noise amplitude for off-Pi development."""

    def __init__(self) -> None:
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self, callback) -> None:
        self._running = True

        def _loop() -> None:
            while self._running:
                # Mostly quiet, with occasional random bumps so downstream
                # logic (jaw sync, loud-noise trigger) has something to react to.
                rms = random.uniform(0.0, 0.05)
                if random.random() < 0.02:
                    rms = random.uniform(0.4, 0.7)
                callback(rms)
                time.sleep(CONFIG.audio.block_size / CONFIG.audio.sample_rate_hz)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)


def _detect_mic_backend() -> MicBackend:
    try:
        return SoundDeviceMicBackend()
    except Exception as exc:  # noqa: BLE001
        logger.info("sounddevice unavailable (%s); using mock mic.", exc)
        return MockMicBackend()


class AudioInput:
    """Streams microphone amplitude in the background; non-blocking reads."""

    def __init__(self, backend: MicBackend | None = None) -> None:
        self._backend = backend or _detect_mic_backend()
        self._latest_rms = 0.0
        self._lock = threading.Lock()
        self._loud_event = threading.Event()
        self._backend.start(self._on_sample)

    def _on_sample(self, rms: float) -> None:
        with self._lock:
            self._latest_rms = rms
        if rms >= CONFIG.audio.loud_noise_threshold:
            self._loud_event.set()

    @property
    def latest_rms(self) -> float:
        """Most recent RMS amplitude reading (thread-safe, non-blocking)."""
        with self._lock:
            return self._latest_rms

    def consume_loud_event(self) -> bool:
        """Return True (and clear the flag) if a loud-noise event fired since
        the last call. Non-blocking.
        """
        if self._loud_event.is_set():
            self._loud_event.clear()
            return True
        return False

    def amplitude_to_jaw_angle(self, rms: float) -> float:
        """Map current mic RMS to a target jaw servo angle."""
        lo = CONFIG.audio.jaw_map_min_amplitude
        hi = CONFIG.audio.jaw_map_max_amplitude
        t = 0.0 if hi <= lo else (rms - lo) / (hi - lo)
        t = max(0.0, min(1.0, t))
        closed = CONFIG.servo.jaw_closed_deg
        open_ = CONFIG.servo.jaw_open_deg
        return closed + t * (open_ - closed)

    def shutdown(self) -> None:
        self._backend.stop()


# ---------------------------------------------------------------------------
# Audio output (pre-recorded playback + TTS), non-blocking via worker thread
# ---------------------------------------------------------------------------

class PlaybackBackend(Protocol):
    """Hardware abstraction for playing a single audio file to completion."""

    def play_file(self, path: Path) -> None:
        ...


class SimpleAudioPlaybackBackend:
    """Real playback backend using `simpleaudio` (WAV) with a fallback to
    the `playsound` package for MP3 if needed."""

    def play_file(self, path: Path) -> None:
        if path.suffix.lower() == ".wav":
            import simpleaudio as sa  # type: ignore

            wave_obj = sa.WaveObject.from_wave_file(str(path))
            play_obj = wave_obj.play()
            play_obj.wait_done()
        else:
            from playsound import playsound  # type: ignore

            playsound(str(path))


class MockPlaybackBackend:
    """Logs playback instead of producing sound."""

    def play_file(self, path: Path) -> None:
        logger.info("MOCK playback: %s", path)
        time.sleep(0.05)  # simulate brief playback for realistic timing


def _detect_playback_backend() -> PlaybackBackend:
    try:
        import simpleaudio  # noqa: F401  # type: ignore

        return SimpleAudioPlaybackBackend()
    except Exception as exc:  # noqa: BLE001
        logger.info("simpleaudio unavailable (%s); using mock playback.", exc)
        return MockPlaybackBackend()


class TTSBackend(Protocol):
    """Hardware abstraction for text-to-speech synthesis + playback."""

    def speak(self, text: str) -> None:
        ...


class Pyttsx3TTSBackend:
    """Real offline TTS backend using `pyttsx3`."""

    def __init__(self) -> None:
        import pyttsx3  # type: ignore

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", CONFIG.lines.tts_voice_rate_wpm)
        if CONFIG.lines.tts_voice_id:
            self._engine.setProperty("voice", CONFIG.lines.tts_voice_id)

    def speak(self, text: str) -> None:
        self._engine.say(text)
        self._engine.runAndWait()


class MockTTSBackend:
    """Logs what would be spoken instead of synthesizing audio."""

    def speak(self, text: str) -> None:
        logger.info("MOCK TTS: %r", text)
        time.sleep(0.05)


def _detect_tts_backend() -> TTSBackend:
    try:
        return Pyttsx3TTSBackend()
    except Exception as exc:  # noqa: BLE001
        logger.info("pyttsx3 unavailable (%s); using mock TTS.", exc)
        return MockTTSBackend()


class AudioOutput:
    """Non-blocking audio output: queues playback/TTS jobs onto a worker
    thread so `main.py`'s control loop never stalls waiting on audio.
    """

    def __init__(
        self,
        playback_backend: PlaybackBackend | None = None,
        tts_backend: TTSBackend | None = None,
    ) -> None:
        self._playback = playback_backend or _detect_playback_backend()
        self._tts = tts_backend or _detect_tts_backend()
        self._queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self) -> None:
        while self._running:
            try:
                kind, payload = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                if kind == "file":
                    self._playback.play_file(CONFIG.lines.audio_dir / payload)
                elif kind == "tts":
                    self._tts.speak(payload)
            except Exception:  # noqa: BLE001
                logger.exception("Audio playback job failed")
            finally:
                self._queue.task_done()

    def play_random_line(self, mode: str) -> None:
        """Queue a random pre-recorded line for the given mode ("host" or
        "trickster"). Non-blocking.
        """
        lines = (
            CONFIG.lines.host_prerecorded
            if mode == "host"
            else CONFIG.lines.trickster_prerecorded
        )
        if lines:
            self._queue.put(("file", random.choice(lines)))

    def speak_random_tts(self, mode: str) -> None:
        """Queue a random spontaneous TTS line for the given mode.
        Non-blocking.
        """
        lines = (
            CONFIG.lines.host_tts_lines
            if mode == "host"
            else CONFIG.lines.trickster_tts_lines
        )
        if lines:
            self._queue.put(("tts", random.choice(lines)))

    def speak_text(self, text: str) -> None:
        """Queue an arbitrary line of TTS text directly, bypassing the
        HOST/TRICKSTER line sets. Used for guest-specific dialogue (see
        `behavior.py`'s `on_guest_recognized` hook) where the actual line
        content comes from `script_lines.py` rather than `config.py`.
        Non-blocking.
        """
        if text:
            self._queue.put(("tts", text))

    def shutdown(self) -> None:
        self._running = False
        self._thread.join(timeout=1.0)
