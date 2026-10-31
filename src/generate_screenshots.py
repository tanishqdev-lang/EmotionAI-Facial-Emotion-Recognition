"""
Generate real prediction screenshots and visual proof for the report and documentation.
"""

import os
import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "assets", "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

from src.prediction import EmotionPredictor
from src.utils import generate_probability_bar_chart, generate_radar_chart, EMOTION_COLOR_MAP


def generate_app_screenshots():
    predictor = EmotionPredictor()
    sample_img_path = os.path.join(PROJECT_ROOT, "assets", "samples", "amazingkelly.jpeg")
    img_bgr = cv2.imread(sample_img_path)
    if img_bgr is None:
        print("Sample image not found!")
        return

    predictions, annotated_bgr = predictor.predict_image(img_bgr)
    annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
    
    # Save standalone annotated detection
    detection_out = os.path.join(SCREENSHOTS_DIR, "detected_face_annotated.png")
    cv2.imwrite(detection_out, annotated_bgr)
    print("Saved:", detection_out)

    # Generate complete composite screenshot simulating the dashboard view
    pred = predictions[0]
    top_emotion = pred["emotion"]
    confidence = pred["confidence"]
    color = EMOTION_COLOR_MAP.get(top_emotion, "#3498DB")

    fig = plt.figure(figsize=(14, 7), facecolor='#0E1117')
    gs = fig.add_gridspec(2, 2, width_ratios=[1.1, 1.2], height_ratios=[1, 1], wspace=0.25, hspace=0.35)

    # 1. Image on the left
    ax_img = fig.add_subplot(gs[:, 0])
    ax_img.imshow(annotated_rgb)
    ax_img.set_title(f"Facial Detection & Classification ({top_emotion.capitalize()} {confidence:.1f}%)",
                     color='#FFFFFF', fontsize=12, fontweight='bold', pad=10)
    ax_img.axis('off')

    # 2. Probability Bar Chart (Top Right)
    ax_bar = fig.add_subplot(gs[0, 1])
    ax_bar.set_facecolor('#1E1E2F')
    emotions = list(pred["probabilities"].keys())
    scores = [pred["probabilities"][e] for e in emotions]
    colors = [EMOTION_COLOR_MAP.get(e, '#3498DB') for e in emotions]
    y_pos = np.arange(len(emotions))
    bars = ax_bar.barh(y_pos, scores, color=colors, height=0.6)
    ax_bar.set_yticks(y_pos)
    ax_bar.set_yticklabels([e.capitalize() for e in emotions], color='#FFFFFF', fontsize=9, fontweight='bold')
    ax_bar.invert_yaxis()
    ax_bar.set_xlim(0, 105)
    ax_bar.tick_params(colors='#FFFFFF', labelsize=8.5)
    ax_bar.set_xlabel('Confidence (%)', color='#FFFFFF', fontsize=9.5, fontweight='bold')
    ax_bar.set_title("Probability Distribution Across 7 Emotion Classes", color='#FFFFFF', fontsize=11, fontweight='bold')
    for spine in ax_bar.spines.values():
        spine.set_visible(False)
    ax_bar.grid(axis='x', linestyle='--', alpha=0.3, color='#4A4A60')
    for b, s in zip(bars, scores):
        ax_bar.text(b.get_width() + 1.5, b.get_y() + b.get_height()/2, f"{s:.1f}%",
                    va='center', color='#FFFFFF', fontsize=8.5, fontweight='bold')

    # 3. Radar Chart (Bottom Right)
    ax_radar = fig.add_subplot(gs[1, 1], polar=True)
    ax_radar.set_facecolor('#1E1E2F')
    rad_vals = scores + scores[:1]
    angles = np.linspace(0, 2 * np.pi, len(emotions), endpoint=False).tolist() + [0]
    ax_radar.plot(angles, rad_vals, color='#6C5CE7', lw=2)
    ax_radar.fill(angles, rad_vals, color='#6C5CE7', alpha=0.35)
    ax_radar.set_xticks(angles[:-1])
    ax_radar.set_xticklabels([e.capitalize() for e in emotions], color='#FFFFFF', fontsize=8, fontweight='bold')
    ax_radar.tick_params(colors='#FFFFFF')
    ax_radar.spines['polar'].set_color('#4A4A60')
    ax_radar.grid(color='#4A4A60', linestyle='--', alpha=0.5)
    ax_radar.set_title("Affective Radar Profile", color='#FFFFFF', fontsize=11, fontweight='bold', pad=12)

    ui_out = os.path.join(SCREENSHOTS_DIR, "dashboard_runtime_screenshot.png")
    plt.savefig(ui_out, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("Saved:", ui_out)


if __name__ == "__main__":
    generate_app_screenshots()
