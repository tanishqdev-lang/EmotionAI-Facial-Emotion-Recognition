"""
Real-Time Desktop Webcam Inference Script (EmotionAI)
Author: Academic Deep Learning Project
Description: Runs high-speed native 30-60 FPS real-time facial emotion recognition
with bounding boxes, emotion labels, and live probability overlays.
Press 'Q' or 'ESC' on your keyboard to close the camera window.
"""

import os
import sys
import time
import cv2
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.prediction import EmotionPredictor, EMOTION_CLASSES
from src.utils import EMOTION_COLOR_MAP

# BGR color mapping for OpenCV drawing
CV_COLORS = {
    'angry': (50, 50, 240),      # Red
    'disgusted': (60, 200, 70),  # Green
    'fearful': (180, 70, 180),   # Purple
    'happy': (40, 220, 255),     # Yellow / Gold
    'sad': (220, 150, 50),       # Blue
    'surprised': (255, 130, 30), # Cyan / Orange
    'neutral': (170, 170, 170)   # Gray
}


def run_realtime_webcam(camera_index: int = 0):
    print("=" * 60)
    print("EMOTIONAI – NATIVE REAL-TIME WEBCAM RECOGNITION")
    print("=" * 60)
    print("Initializing Deep CNN inference engine...")
    predictor = EmotionPredictor()
    print("Model loaded successfully!")

    print(f"Opening Video Camera (Device Index: {camera_index})...")
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera device {camera_index}.")
        print("Please check that your webcam is connected and not locked by another application (e.g., Zoom, Teams, Skype, or Windows Camera app).")
        return

    # Set camera resolution to 640x480 for fast responsive processing
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Camera connected successfully!")
    print("Press 'Q' or 'ESC' on the video window to quit.")
    print("-" * 60)

    fps_time = time.time()
    frame_count = 0
    fps = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab camera frame. Exiting...")
            break

        frame_count += 1
        if frame_count % 5 == 0:
            fps = 5.0 / max(0.001, time.time() - fps_time)
            fps_time = time.time()

        # Run face detection and emotion prediction
        predictions, annotated = predictor.predict_image(frame)

        # Draw HUD overlays on annotated frame
        cv2.putText(
            annotated,
            f"EmotionAI Real-Time | FPS: {fps:.1f}",
            (16, 28),
            cv2.FONT_HERSHEY_DUPLEX,
            0.65,
            (0, 255, 128),
            1,
            cv2.LINE_AA
        )

        # If a face is detected, draw mini probability bars in the top-right corner
        if predictions:
            top_pred = predictions[0]
            probs = top_pred["probabilities"]
            box_x = annotated.shape[1] - 180
            box_y = 15

            # Background translucent panel
            overlay = annotated.copy()
            cv2.rectangle(overlay, (box_x - 10, box_y - 5), (annotated.shape[1] - 10, box_y + 165), (20, 20, 25), -1)
            cv2.addWeighted(overlay, 0.75, annotated, 0.25, 0, annotated)

            for idx, (emo, score) in enumerate(probs.items()):
                y_pos = box_y + idx * 22 + 16
                clr = CV_COLORS.get(emo, (200, 200, 200))
                # Label
                cv2.putText(annotated, emo[:4].upper(), (box_x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
                # Bar
                bar_len = int((score / 100.0) * 80)
                cv2.rectangle(annotated, (box_x + 45, y_pos - 8), (box_x + 45 + bar_len, y_pos + 1), clr, -1)
                # Value
                cv2.putText(annotated, f"{score:.0f}%", (box_x + 132, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (220, 220, 220), 1)

        cv2.imshow("EmotionAI – Real-Time Facial Emotion Recognition (Press 'Q' to Exit)", annotated)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q') or key == 27: # 27 is ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Camera stream closed.")


if __name__ == "__main__":
    cam_id = 0
    if len(sys.argv) > 1:
        try:
            cam_id = int(sys.argv[1])
        except ValueError:
            pass
    run_realtime_webcam(cam_id)
