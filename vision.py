"""
vision.py

Face detection and tracking via the Raspberry Pi Camera, producing a
smoothed target head-servo angle and a normalized "closeness" value for
LED brightness scaling.

Zero 2 W performance note: Haar-cascade detection is the heaviest single
operation in the control loop. To keep the loop responsive on a
single-1GHz-quad-core board, `FaceTracker.read()` only runs detection on
every `CONFIG.vision.detect_every_n_frames`-th call; on skipped frames it
returns the last known (still-easing) target rather than a fresh
detection. This trades a bit of tracking freshness for a loop that
doesn't stutter.
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
    """One frame's worth of face-tracking output."""

    face_found: bool
    horizontal_offset: float  # normalized [-1.0, 1.0]
    closeness: float          # normalized [0.0, 1.0]


class CameraSource(Protocol):
    def read_frame(self) -> np.ndarray | None: ...
    def close(self) -> None: ...


class PiCameraSource:
    """Real hardware source using picamera2.

    Works with any Camera Module (v1/v2/v3) — the important part for a
    Zero 2 W build is the physical cable, not the software: you need a
    "Raspberry Pi Zero camera cable" (narrow-to-narrow or standard-to-narrow
    depending on your camera board), since the Zero 2 W's CSI connector is
    the small-format one. The software here doesn't need to know which
    cable you used.
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


class FaceTracker:
    """Detects faces and produces smoothed tracking targets."""

    def __init__(self, source: CameraSource | None = None) -> None:
        self._source = source or _detect_camera_source()
        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._smoothed_offset = 0.0
        self._smoothed_closeness = 0.0
        self._last_face_found = False
        self._frame_counter = 0

    def read(self, smoothing: float) -> TrackingResult:
        """Grab a frame and, on detection frames, update the smoothed
        tracking target. On skipped frames, returns the last known target
        so the caller can keep easing toward it without stalling.
        """
        frame = self._source.read_frame()
        if frame is None:
            return TrackingResult(False, self._smoothed_offset, self._smoothed_closeness)

        self._frame_counter += 1
        run_detection = (self._frame_counter % max(1, CONFIG.vision.detect_every_n_frames)) == 0
        if not run_detection:
            return TrackingResult(
                self._last_face_found, self._smoothed_offset, self._smoothed_closeness
            )

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=CONFIG.vision.detection_scale_factor,
            minNeighbors=CONFIG.vision.detection_min_neighbors,
        )

        if len(faces) == 0:
            self._last_face_found = False
            return TrackingResult(False, self._smoothed_offset, self._smoothed_closeness)

        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        frame_h, frame_w = gray.shape[:2]

        face_center_x = x + w / 2.0
        raw_offset = (face_center_x - frame_w / 2.0) / (frame_w / 2.0)
        raw_offset = max(-1.0, min(1.0, raw_offset))

        raw_closeness = min(1.0, h / CONFIG.vision.close_face_bbox_height_px)

        smoothing = max(0.0, min(1.0, smoothing))
        self._smoothed_offset += (raw_offset - self._smoothed_offset) * smoothing
        self._smoothed_closeness += (raw_closeness - self._smoothed_closeness) * smoothing
        self._last_face_found = True

        return TrackingResult(True, self._smoothed_offset, self._smoothed_closeness)

    def offset_to_head_angle(self, offset: float) -> float:
        span = (CONFIG.servo.head_max_deg - CONFIG.servo.head_min_deg) / 2.0
        return CONFIG.servo.head_center_deg + offset * span

    def close(self) -> None:
        self._source.close()
