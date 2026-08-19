"""
vision.py

Face detection and tracking via the Raspberry Pi Camera, producing
smoothed target pan/tilt servo angles, a normalized "closeness" value for
LED brightness scaling, and (when a trained model is available) guest
face recognition via LBPH.

Performance note: Haar-cascade detection is the heaviest single operation
in the control loop. To keep the loop responsive, `FaceTracker.read()`
only runs detection on every `CONFIG.vision.detect_every_n_frames`-th
call; on skipped frames it returns the last known (still-easing) target
rather than a fresh detection. This trades a bit of tracking freshness
for a loop that doesn't stutter. (Originally tuned as a necessity for the
Zero 2 W's CPU; kept as a sane default on the Pi 4, which has headroom to
spare.)

Face recognition (LBPH, via opencv-contrib-python's `cv2.face` module) is
treated as fully optional: if the library or trained model files aren't
present, `FaceTracker` falls back to tracking-only mode automatically —
per the project's graceful-degradation principle, missing recognition
data should never block basic face tracking.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import cv2
import numpy as np

from config import CONFIG

logger = logging.getLogger(__name__)


@dataclass
class TrackingResult:
    """One frame's worth of face-tracking (and optional recognition) output."""

    face_found: bool
    horizontal_offset: float           # normalized [-1.0, 1.0], for pan
    vertical_offset: float             # normalized [-1.0, 1.0], for tilt
    closeness: float                   # normalized [0.0, 1.0]
    identified_guest: str | None = None       # guest key, or None if unrecognized/no model
    recognition_confidence: float | None = None  # LBPH distance; LOWER = better match


class CameraSource(Protocol):
    def read_frame(self) -> np.ndarray | None: ...
    def close(self) -> None: ...


class PiCameraSource:
    """Real hardware source using picamera2.

    Works with any Camera Module (v2/v3 recommended). On the Pi 4, the
    Camera Module 3's stock CSI cable plugs in directly — no narrow-CSI
    adapter needed (that was a Pi Zero 2 W–specific requirement).
    """

    def __init__(self) -> None:
        from picamera2 import Picamera2  # type: ignore

        self._cam = Picamera2()
        config = self._cam.create_preview_configuration(
            main={
                "size": (CONFIG.vision.frame_width, CONFIG.vision.frame_height),
                "format": "RGB888",
            }
        )
        self._cam.configure(config)
        self._cam.start()

    def read_frame(self) -> np.ndarray | None:
        frame = self._cam.capture_array()
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    def close(self) -> None:
        self._cam.stop()


class WebcamSource:
    """Fallback source using any OpenCV-compatible webcam (dev machines)."""

    def __init__(self, device_index: int = 0) -> None:
        self._cap = cv2.VideoCapture(device_index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG.vision.frame_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG.vision.frame_height)
        if not self._cap.isOpened():
            raise RuntimeError("No webcam available")

    def read_frame(self) -> np.ndarray | None:
        ok, frame = self._cap.read()
        return frame if ok else None

    def close(self) -> None:
        self._cap.release()


class MockCameraSource:
    """Synthetic source for testing without any camera hardware."""

    def __init__(self) -> None:
        self._frame = np.zeros(
            (CONFIG.vision.frame_height, CONFIG.vision.frame_width, 3),
            dtype=np.uint8,
        )

    def read_frame(self) -> np.ndarray | None:
        return self._frame

    def close(self) -> None:
        pass


def _detect_camera_source() -> CameraSource:
    try:
        return PiCameraSource()
    except Exception as exc:  # noqa: BLE001
        logger.info("picamera2 unavailable (%s); trying webcam.", exc)
    try:
        return WebcamSource()
    except Exception as exc:  # noqa: BLE001
        logger.info("Webcam unavailable (%s); using mock camera source.", exc)
        return MockCameraSource()


# ---------------------------------------------------------------------------
# Face recognition (LBPH)
# ---------------------------------------------------------------------------

class FaceRecognizerBackend(Protocol):
    """Hardware/library abstraction for identifying a cropped face image."""

    def identify(self, face_gray: np.ndarray) -> tuple[str | None, float | None]:
        """Return (guest_key, confidence) for a grayscale face crop.

        `confidence` is an LBPH distance (lower = better match); the
        caller is responsible for applying `CONFIG.recognition
        .confidence_threshold`. Returns (None, None) if nothing could be
        identified (e.g. no model loaded).
        """
        ...


class LBPHFaceRecognizerBackend:
    """Real recognizer backend using OpenCV's LBPH face recognizer.

    Requires `opencv-contrib-python` (for `cv2.face`) and a previously
    trained model (`train_recognizer.py`) written to
    `CONFIG.recognition.model_path` / `label_map_path`. Raises on
    construction if either precondition isn't met, so
    `_detect_recognizer_backend()` can fall back to tracking-only mode
    cleanly.
    """

    def __init__(self) -> None:
        if not hasattr(cv2, "face"):
            raise RuntimeError(
                "cv2.face not available - install opencv-contrib-python"
            )
        model_path = CONFIG.recognition.model_path
        label_map_path = CONFIG.recognition.label_map_path
        if not model_path.exists() or not label_map_path.exists():
            raise RuntimeError(
                f"Trained model not found ({model_path}, {label_map_path}) - "
                "run enroll_faces.py then train_recognizer.py first"
            )

        import json

        self._recognizer = cv2.face.LBPHFaceRecognizer_create()
        self._recognizer.read(str(model_path))

        with open(label_map_path, "r", encoding="utf-8") as f:
            raw_map = json.load(f)
        # label_map.json maps numeric LBPH label IDs (as strings, since
        # JSON keys are always strings) to guest keys, e.g. {"0": "joe"}.
        self._label_map: dict[int, str] = {int(k): v for k, v in raw_map.items()}

    def identify(self, face_gray: np.ndarray) -> tuple[str | None, float | None]:
        sample = cv2.resize(face_gray, CONFIG.recognition.face_sample_size)
        label_id, confidence = self._recognizer.predict(sample)
        guest_key = self._label_map.get(label_id)
        return guest_key, float(confidence)


class NullFaceRecognizerBackend:
    """No-op recognizer used when LBPH isn't available or untrained.

    Keeps the system fully functional in tracking-only mode.
    """

    def identify(self, face_gray: np.ndarray) -> tuple[str | None, float | None]:
        return None, None


def _detect_recognizer_backend() -> FaceRecognizerBackend:
    try:
        return LBPHFaceRecognizerBackend()
    except Exception as exc:  # noqa: BLE001
        logger.info("Face recognizer unavailable (%s); tracking-only mode.", exc)
        return NullFaceRecognizerBackend()


# ---------------------------------------------------------------------------
# Face tracking
# ---------------------------------------------------------------------------

class FaceTracker:
    """Detects faces, produces smoothed pan/tilt tracking targets, and
    (optionally) identifies known guests.
    """

    def __init__(
        self,
        source: CameraSource | None = None,
        recognizer: FaceRecognizerBackend | None = None,
    ) -> None:
        self._source = source or _detect_camera_source()
        self._recognizer = recognizer or _detect_recognizer_backend()
        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._smoothed_offset = 0.0
        self._smoothed_v_offset = 0.0
        self._smoothed_closeness = 0.0
        self._last_face_found = False
        self._frame_counter = 0

    def read(self, smoothing: float) -> TrackingResult:
        """Grab a frame and, on detection frames, update the smoothed
        tracking target (and run recognition on the detected face). On
        skipped frames, returns the last known target so the caller can
        keep easing toward it without stalling.
        """
        frame = self._source.read_frame()
        if frame is None:
            return TrackingResult(
                False, self._smoothed_offset, self._smoothed_v_offset,
                self._smoothed_closeness,
            )

        self._frame_counter += 1
        run_detection = (self._frame_counter % max(1, CONFIG.vision.detect_every_n_frames)) == 0
        if not run_detection:
            return TrackingResult(
                self._last_face_found, self._smoothed_offset, self._smoothed_v_offset,
                self._smoothed_closeness,
            )

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=CONFIG.vision.detection_scale_factor,
            minNeighbors=CONFIG.vision.detection_min_neighbors,
        )

        if len(faces) == 0:
            self._last_face_found = False
            return TrackingResult(
                False, self._smoothed_offset, self._smoothed_v_offset,
                self._smoothed_closeness,
            )

        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        frame_h, frame_w = gray.shape[:2]

        face_center_x = x + w / 2.0
        raw_offset = (face_center_x - frame_w / 2.0) / (frame_w / 2.0)
        raw_offset = max(-1.0, min(1.0, raw_offset))

        face_center_y = y + h / 2.0
        # Positive = face is below frame center -> tilt servo should angle
        # down to follow it. Flip the sign here if your servo/mount
        # orientation makes it track backwards in practice.
        raw_v_offset = (face_center_y - frame_h / 2.0) / (frame_h / 2.0)
        raw_v_offset = max(-1.0, min(1.0, raw_v_offset))

        raw_closeness = min(1.0, h / CONFIG.vision.close_face_bbox_height_px)

        smoothing = max(0.0, min(1.0, smoothing))
        self._smoothed_offset += (raw_offset - self._smoothed_offset) * smoothing
        self._smoothed_v_offset += (raw_v_offset - self._smoothed_v_offset) * smoothing
        self._smoothed_closeness += (raw_closeness - self._smoothed_closeness) * smoothing
        self._last_face_found = True

        face_roi = gray[y:y + h, x:x + w]
        guest_key, confidence = self._recognizer.identify(face_roi)
        identified_guest = None
        if (
            guest_key is not None
            and confidence is not None
            and confidence <= CONFIG.recognition.confidence_threshold
        ):
            identified_guest = guest_key

        return TrackingResult(
            True,
            self._smoothed_offset,
            self._smoothed_v_offset,
            self._smoothed_closeness,
            identified_guest,
            confidence,
        )

    def offset_to_head_angle(self, offset: float) -> float:
        """Map a horizontal tracking offset to a pan servo angle."""
        span = (CONFIG.servo.head_max_deg - CONFIG.servo.head_min_deg) / 2.0
        return CONFIG.servo.head_center_deg + offset * span

    def offset_to_tilt_angle(self, offset: float) -> float:
        """Map a vertical tracking offset to a tilt servo angle."""
        span = (CONFIG.servo.tilt_max_deg - CONFIG.servo.tilt_min_deg) / 2.0
        return CONFIG.servo.tilt_center_deg + offset * span

    def close(self) -> None:
        self._source.close()
