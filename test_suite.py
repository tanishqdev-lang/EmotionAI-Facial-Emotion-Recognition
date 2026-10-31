"""
End-to-End Verification Test Suite for EmotionAI
Author: Senior ML Engineer
Description: Verifies model loading, dual-engine inference, preprocessing,
error handling, and file integrity.
"""

import os
import sys
import numpy as np
import cv2

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.preprocessing import FacePreprocessor
from src.prediction import EmotionPredictor, EMOTION_CLASSES
from src.utils import generate_probability_bar_chart, generate_radar_chart, get_benchmark_metrics_dataframe


def run_tests():
    print("=" * 60)
    print("EMOTIONAI COMPREHENSIVE SYSTEM VERIFICATION")
    print("=" * 60)

    # 1. Test Model Loading (Default Engine)
    print("[1/6] Testing Model Loading (Default Engine)...")
    predictor = EmotionPredictor()
    assert len(predictor.weights) == 10, "Should have 10 weight tensors loaded"
    print("  -> Passed: All 10 layer tensors loaded correctly.")

    # 2. Test Pure Vectorized NumPy Engine explicitly
    print("[2/6] Testing Pure Vectorized NumPy Engine...")
    pred_np = EmotionPredictor(use_tf=False)
    dummy_input = np.ones((1, 2304), dtype=np.float32) * 0.5
    res_np = pred_np.predict_tensor(dummy_input)
    assert res_np["emotion"] in EMOTION_CLASSES, "Predicted emotion must be valid"
    assert sum(res_np["probabilities"].values()) > 99.0, "Probabilities must sum to ~100%"
    print(f"  -> Passed: NumPy engine inference returned '{res_np['emotion']}' with {res_np['confidence']:.2f}% confidence.")

    # 3. Test Preprocessing & Face Detection on Benchmark Sample
    print("[3/6] Testing Preprocessing & Face Detection on 'happy_tg.jpg'...")
    preprocessor = FacePreprocessor()
    sample_path = os.path.join(PROJECT_ROOT, "assets", "samples", "happy_tg.jpg")
    img_bgr = cv2.imread(sample_path)
    assert img_bgr is not None, "Sample image happy_tg.jpg must exist"

    rois = preprocessor.extract_face_rois(img_bgr)
    assert len(rois) > 0, "At least one face ROI must be extracted"
    print(f"  -> Passed: Detected {len(rois)} face(s). First face ROI shape: {rois[0]['face_resized'].shape}")

    # 4. Test End-to-End Prediction Pipeline
    print("[4/6] Testing End-to-End Prediction on Sample...")
    predictions, annotated_bgr = predictor.predict_image(img_bgr)
    assert len(predictions) > 0, "Must return predictions"
    top_pred = predictions[0]
    print(f"  -> Passed: Top Emotion: {top_pred['emotion'].capitalize()} ({top_pred['confidence']:.2f}%)")
    assert top_pred['emotion'] == 'happy', "happy_tg.jpg must be classified as 'happy'"
    assert annotated_bgr.shape == img_bgr.shape, "Annotated image dimensions must match input"

    # 5. Test Robust Error Handling & Fallback
    print("[5/6] Testing Robust Error Handling & Fallback...")
    blank_canvas = np.zeros((200, 200, 3), dtype=np.uint8)
    blank_preds, _ = predictor.predict_image(blank_canvas)
    assert len(blank_preds) > 0, "Fallback must handle face-less images without crashing"
    assert blank_preds[0]["is_fallback"] is True, "Fallback flag must be set to True"
    print("  -> Passed: Fallback mechanism handled face-less canvas gracefully.")

    # 6. Test Visualization & Metrics Utilities
    print("[6/6] Testing Visualization Generators & Benchmark Metrics...")
    fig_bar = generate_probability_bar_chart(top_pred["probabilities"], top_pred["emotion"], dark_mode=True)
    assert fig_bar is not None, "Bar chart figure must generate"
    fig_radar = generate_radar_chart(top_pred["probabilities"], dark_mode=True)
    assert fig_radar is not None, "Radar chart figure must generate"
    df_metrics = get_benchmark_metrics_dataframe()
    assert len(df_metrics) == 7, "Metrics table must cover all 7 emotion classes"
    print("  -> Passed: All visualization figures and benchmark dataframes compiled.")

    print("=" * 60)
    print("ALL 6 TEST SUITES PASSED FLAWLESSLY! SYSTEM READY FOR SUBMISSION.")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
