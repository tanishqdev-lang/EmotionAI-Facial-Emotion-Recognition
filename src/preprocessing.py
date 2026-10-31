"""
Preprocessing Module for Facial Emotion Recognition System (EmotionAI)
Author: Academic Deep Learning Project
Description: Robust image loading, face detection, cropping, normalization,
and bounding-box rendering for single and multi-face emotion inference.
"""

import os
from typing import List, Tuple, Optional, Dict, Any
import cv2
import numpy as np
from PIL import Image

# Default Cascade Path
DEFAULT_CASCADE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "haarcascade", "haarcascade_frontalface_default.xml"
)

# Standard target dimensions for FER-2013 deep learning model
TARGET_IMAGE_SIZE = (48, 48)


class FacePreprocessor:
    """Handles face detection, alignment, cropping, and mathematical normalization."""

    def __init__(self, cascade_path: Optional[str] = None):
        """Initialize the Haar Cascade face detector."""
        self.cascade_path = cascade_path or DEFAULT_CASCADE_PATH
        if not os.path.exists(self.cascade_path):
            # Attempt to use cv2 internal data if local file is missing
            self.cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        
        self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
        if self.face_cascade.empty():
            raise RuntimeError(f"Failed to load OpenCV face cascade from {self.cascade_path}")

    def detect_faces(
        self,
        image_bgr: np.ndarray,
        scale_factor: float = 1.15,
        min_neighbors: int = 5,
        min_size: Tuple[int, int] = (30, 30)
    ) -> List[Tuple[int, int, int, int]]:
        """
        Detect all faces in an input BGR image.
        Returns list of bounding boxes: (x, y, w, h).
        """
        if image_bgr is None or image_bgr.size == 0:
            return []

        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY) if len(image_bgr.shape) == 3 else image_bgr
        # Equalize histogram for contrast enhancement
        equalized = cv2.equalizeHist(gray)
        
        faces = self.face_cascade.detectMultiScale(
            equalized,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=min_size,
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Convert numpy array of rects to python list of tuples
        return [tuple(f) for f in faces] if len(faces) > 0 else []

    def extract_face_rois(
        self,
        image_bgr: np.ndarray,
        padding_ratio: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Detect and extract normalized 48x48 face regions of interest (ROIs).
        
        Returns a list of dictionaries with:
          - 'box': (x, y, w, h)
          - 'face_bgr': cropped BGR face
          - 'face_gray': cropped grayscale face
          - 'face_resized': 48x48 grayscale image
          - 'tensor': flattened float32 array normalized to [0, 1] (shape: (1, 2304))
          - 'tensor_4d': 4D tensor (1, 48, 48, 1) normalized to [0, 1]
        """
        if image_bgr is None or image_bgr.size == 0:
            return []

        h_img, w_img = image_bgr.shape[:2]
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY) if len(image_bgr.shape) == 3 else image_bgr.copy()
        face_boxes = self.detect_faces(image_bgr)

        # If no face is detected by cascade, fall back to center crop with warning flag
        used_fallback = False
        if not face_boxes:
            min_dim = min(h_img, w_img)
            start_x = (w_img - min_dim) // 2
            start_y = (h_img - min_dim) // 2
            face_boxes = [(start_x, start_y, min_dim, min_dim)]
            used_fallback = True

        results = []
        for (x, y, w, h) in face_boxes:
            # Apply padding around face detection if within bounds
            pad_w = int(w * padding_ratio)
            pad_h = int(h * padding_ratio)
            x1 = max(0, x - pad_w)
            y1 = max(0, y - pad_h)
            x2 = min(w_img, x + w + pad_w)
            y2 = min(h_img, y + h + pad_h)

            face_crop_gray = gray[y1:y2, x1:x2]
            face_crop_bgr = image_bgr[y1:y2, x1:x2] if len(image_bgr.shape) == 3 else cv2.cvtColor(face_crop_gray, cv2.COLOR_GRAY2BGR)

            if face_crop_gray.size == 0:
                continue

            # Resize to network dimensions (48, 48) using bicubic interpolation
            resized = cv2.resize(face_crop_gray, TARGET_IMAGE_SIZE, interpolation=cv2.INTER_CUBIC)

            # Normalization: pixel values scaled to [0.0, 1.0] as expected by the FER-2013 model
            norm_tensor = resized.astype(np.float32) / 255.0
            flat_tensor = norm_tensor.reshape(1, 2304)
            tensor_4d = norm_tensor.reshape(1, 48, 48, 1)

            results.append({
                "box": (x, y, w, h),
                "padded_box": (x1, y1, x2 - x1, y2 - y1),
                "face_bgr": face_crop_bgr,
                "face_gray": face_crop_gray,
                "face_resized": resized,
                "tensor": flat_tensor,
                "tensor_4d": tensor_4d,
                "is_fallback": used_fallback
            })

        return results

    @staticmethod
    def draw_predictions_on_image(
        image_bgr: np.ndarray,
        predictions: List[Dict[str, Any]],
        color_map: Optional[Dict[str, Tuple[int, int, int]]] = None
    ) -> np.ndarray:
        """
        Draw aesthetic bounding boxes, emotion labels, and confidence tags on the image.
        """
        output = image_bgr.copy()
        default_colors = {
            "angry": (36, 36, 230),       # Red
            "disgusted": (40, 180, 80),   # Green
            "fearful": (180, 50, 180),    # Purple
            "happy": (40, 215, 255),      # Gold / Yellow
            "sad": (220, 140, 40),        # Deep Blue
            "surprised": (255, 120, 0),   # Cyan / Blue
            "neutral": (160, 160, 160),   # Gray
        }
        palette = color_map or default_colors

        for pred in predictions:
            box = pred.get("box", (0, 0, 0, 0))
            emotion = pred.get("emotion", "unknown")
            confidence = pred.get("confidence", 0.0)

            x, y, w, h = box
            color = palette.get(emotion.lower(), (0, 255, 128))

            # Bounding rectangle with corner accents
            cv2.rectangle(output, (x, y), (x + w, y + h), color, 2)
            corner_len = max(12, int(w * 0.15))
            thick = 3
            # Top-left corner
            cv2.line(output, (x, y), (x + corner_len, y), color, thick)
            cv2.line(output, (x, y), (x, y + corner_len), color, thick)
            # Top-right corner
            cv2.line(output, (x + w, y), (x + w - corner_len, y), color, thick)
            cv2.line(output, (x + w, y), (x + w, y + corner_len), color, thick)
            # Bottom-left corner
            cv2.line(output, (x, y + h), (x + corner_len, y + h), color, thick)
            cv2.line(output, (x, y + h), (x, y + h - corner_len), color, thick)
            # Bottom-right corner
            cv2.line(output, (x + w, y + h), (x + w - corner_len, y + h), color, thick)
            cv2.line(output, (x + w, y + h), (x + w, y + h - corner_len), color, thick)

            # Label banner
            label = f"{emotion.capitalize()} ({confidence:.1f}%)"
            font = cv2.FONT_HERSHEY_DUPLEX
            font_scale = 0.6
            (lbl_w, lbl_h), baseline = cv2.getTextSize(label, font, font_scale, 1)

            banner_y1 = max(0, y - lbl_h - 10)
            banner_y2 = y
            cv2.rectangle(output, (x, banner_y1), (x + lbl_w + 14, banner_y2), color, -1)
            cv2.putText(
                output,
                label,
                (x + 7, banner_y2 - 5),
                font,
                font_scale,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        return output
