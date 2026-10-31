"""
EmotionAI – Facial Emotion Recognition System
===================================================
A modern, production-grade AI dashboard for real-time facial expression
detection and affective computing using Deep Convolutional Neural Networks.
"""

import os
import sys
import time
from datetime import datetime
from PIL import Image
import cv2
import numpy as np
import pandas as pd
import streamlit as st

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.prediction import EmotionPredictor, EMOTION_CLASSES, EMOTION_UNICODE
from src.preprocessing import FacePreprocessor
from src.utils import (
    generate_probability_bar_chart,
    generate_radar_chart,
    generate_confusion_matrix_figure,
    get_benchmark_metrics_dataframe,
    EMOTION_COLOR_MAP
)

# Set Page Config
st.set_page_config(
    page_title="EmotionAI – Facial Emotion Recognition",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern AI Dashboard Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6C5CE7 0%, #a29bfe 50%, #00cec9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    .sub-title {
        color: #8395a7;
        font-size: 1.05rem;
        margin-bottom: 1.6rem;
    }

    .metric-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        margin-bottom: 15px;
    }

    .emotion-badge {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 30px;
        font-weight: 700;
        font-size: 1.3rem;
        letter-spacing: 0.5px;
        text-transform: capitalize;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }

    .stat-label {
        color: #a4b0be;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }

    .stat-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #ffffff;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Initializing Neural Inference Engine...")
def load_emotion_predictor():
    """Load model once and cache across user sessions."""
    return EmotionPredictor()


def init_session_state():
    """Initialize session state variables for prediction history and settings."""
    if "history" not in st.session_state:
        st.session_state.history = []
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    if "camera_streaming" not in st.session_state:
        st.session_state.camera_streaming = False


def add_to_history(emotion: str, confidence: float, source: str):
    """Log prediction event into session memory."""
    st.session_state.history.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "source": source,
        "emotion": emotion.capitalize(),
        "confidence": f"{confidence:.1f}%",
        "unicode": EMOTION_UNICODE.get(emotion.lower(), "🙂")
    })


def render_prediction_results(predictions, original_img, annotated_img, source="Upload", key_prefix="default"):
    """Render prediction metrics, visualizations, and emotional analysis with unique widget keys."""
    if not predictions:
        st.warning("⚠️ No face was detected in this frame. Please ensure proper lighting and face alignment.")
        st.image(original_img, caption="Source Image", use_container_width=True)
        return

    # Two column layout: Annotated Image vs Affective Analytics
    col_img, col_metrics = st.columns([1.1, 1.3], gap="large")

    with col_img:
        st.subheader("📸 Facial Detection")
        st.image(annotated_img, caption=f"Detected {len(predictions)} face(s)", use_container_width=True)

        if len(predictions) > 1:
            st.info(f"💡 Multi-face mode active: Analyzed **{len(predictions)}** distinct faces.")

    with col_metrics:
        # If multiple faces, allow user to inspect individual faces with a unique key
        if len(predictions) > 1:
            face_labels = [f"Face #{i+1} – {p['emotion'].capitalize()} ({p['confidence']:.1f}%)" for i, p in enumerate(predictions)]
            selected_idx = st.selectbox(
                "Select Face to Inspect:",
                range(len(predictions)),
                format_func=lambda x: face_labels[x],
                key=f"select_face_{key_prefix}"
            )
            active_pred = predictions[selected_idx]
        else:
            active_pred = predictions[0]

        top_emotion = active_pred["emotion"]
        confidence = active_pred["confidence"]
        color = EMOTION_COLOR_MAP.get(top_emotion.lower(), "#3498DB")

        # Log into session history
        add_to_history(top_emotion, confidence, source)

        # Primary Emotion Card
        st.markdown(f"""
        <div class="metric-card" style="border-left: 6px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="stat-label">Primary Detected Emotion</div>
                    <div style="margin-top: 6px;">
                        <span class="emotion-badge" style="background: {color}22; color: {color}; border: 1px solid {color};">
                            {active_pred['unicode']} {top_emotion.capitalize()}
                        </span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div class="stat-label">Model Confidence</div>
                    <div class="stat-value" style="color: {color};">{confidence:.1f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Top-3 breakdown metrics
        st.markdown("<div class='stat-label'>Affective Ranking (Top 3)</div>", unsafe_allow_html=True)
        m_col1, m_col2, m_col3 = st.columns(3)
        top_3 = active_pred["top_3"]
        for col, (emo, score) in zip([m_col1, m_col2, m_col3], top_3):
            with col:
                st.metric(
                    label=f"{EMOTION_UNICODE.get(emo, '•')} {emo.capitalize()}",
                    value=f"{score:.1f}%"
                )

        # Interactive Visual Probability Distribution
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        chart_view = st.radio(
            "Visualization Mode:",
            ["📊 Probability Distribution", "🕸️ Affective Radar"],
            horizontal=True,
            key=f"chart_view_{key_prefix}"
        )
        
        if "Probability" in chart_view:
            fig_bar = generate_probability_bar_chart(
                active_pred["probabilities"],
                top_emotion,
                dark_mode=st.session_state.dark_mode
            )
            st.pyplot(fig_bar, use_container_width=True)
        else:
            fig_radar = generate_radar_chart(
                active_pred["probabilities"],
                dark_mode=st.session_state.dark_mode
            )
            st.pyplot(fig_radar, use_container_width=True)


def main():
    init_session_state()
    predictor = load_emotion_predictor()

    # Sidebar Navigation and Configuration
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/brain.png", width=90)
        st.markdown("### **EmotionAI Control Hub**")
        st.caption("Deep Learning Facial Affect Recognition")
        
        st.markdown("---")
        theme_toggle = st.toggle("Dark Visualization Theme", value=st.session_state.dark_mode)
        st.session_state.dark_mode = theme_toggle

        st.markdown("#### **Model Specifications**")
        st.markdown("""
        - **Architecture:** Custom Deep CNN (`deepnn`)
        - **Input Layer:** 48 × 48 × 1 (Grayscale)
        - **Trainable Parameters:** 3,653,191 (~3.7M)
        - **Training Dataset:** FER-2013 (35,887 images)
        - **Benchmark Accuracy:** ~65.2%
        - **Active Classes:** 7 Emotions
        """)

        st.markdown("---")
        st.markdown("#### **Affective Classes**")
        for cls_name in EMOTION_CLASSES:
            clr = EMOTION_COLOR_MAP.get(cls_name, "#FFFFFF")
            ico = EMOTION_UNICODE.get(cls_name, "•")
            st.markdown(f"<span style='color: {clr}; font-weight: 600;'>{ico} {cls_name.capitalize()}</span>", unsafe_allow_html=True)

        st.markdown("---")
        st.caption("EmotionAI Academic Project | Deep Learning & Vision")

    # Header Section
    st.markdown("<h1 class='main-title'>EmotionAI – Facial Emotion Recognition</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>High-Accuracy Facial Expression Analysis and Affective Computing powered by Deep Convolutional Neural Networks</p>", unsafe_allow_html=True)

    # Primary App Navigation Tabs
    tab_upload, tab_camera, tab_samples, tab_analytics, tab_history, tab_about = st.tabs([
        "📤 Image Upload",
        "📹 Real-Time Camera",
        "🖼️ Sample Gallery",
        "📈 Model Analytics",
        "🕒 Session History",
        "ℹ️ About Project"
    ])

    # TAB 1: IMAGE UPLOAD
    with tab_upload:
        st.markdown("#### Upload a Portrait or Group Photo")
        st.caption("Supported image formats: JPG, JPEG, PNG. Supports single and multi-face emotion classification.")

        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
            key="file_uploader_widget"
        )
        if uploaded_file is not None:
            try:
                pil_img = Image.open(uploaded_file).convert("RGB")
                img_np = np.array(pil_img)
                img_bgr = img_np[:, :, ::-1].copy()

                with st.spinner("Analyzing facial expressions..."):
                    predictions, annotated_bgr = predictor.predict_image(img_bgr)
                    annotated_rgb = annotated_bgr[:, :, ::-1]

                render_prediction_results(predictions, pil_img, annotated_rgb, source="Upload", key_prefix="upload")
            except Exception as e:
                st.error(f"Error processing uploaded image: {e}")

    # TAB 2: REAL-TIME WEBCAM (DUAL MODES)
    with tab_camera:
        st.markdown("#### Real-Time Facial Emotion Recognition via Camera")
        st.caption("Select your preferred camera mode below:")

        cam_mode = st.radio(
            "Camera Mode Selection:",
            ["🔴 Live Video Stream (Continuous Webcam Feed)", "📸 Browser Camera Snapshot (Single Capture)"],
            horizontal=True,
            key="cam_mode_radio"
        )

        # MODE 1: CONTINUOUS LIVE WEBCAM STREAM
        if "Live Video Stream" in cam_mode:
            st.markdown("---")
            col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1.5, 1.5, 3])
            
            with col_ctrl1:
                cam_index = st.selectbox("Select Camera Device Index:", [0, 1, 2], index=0, key="cam_device_idx")
            with col_ctrl2:
                stream_active = st.checkbox("▶️ Start Live Webcam Stream", value=False, key="stream_toggle")

            frame_placeholder = st.empty()
            metric_placeholder = st.empty()

            if stream_active:
                cap = cv2.VideoCapture(cam_index)
                # Allow camera to warm up
                if not cap.isOpened():
                    st.error(f"❌ Could not access Camera Index {cam_index}. Please verify that the camera is plugged in and not currently open in another program (e.g. Zoom, Teams, Skype, or Windows Camera app).")
                else:
                    st.success("🟢 Camera connected! Streaming live video... (Uncheck the box above to stop)")
                    stop_button = st.button("⏹️ Stop Stream Now", key="stop_stream_btn")

                    fps_time = time.time()
                    while stream_active and not stop_button:
                        ret, frame = cap.read()
                        if not ret:
                            st.warning("Failed to grab video frame. Reconnecting...")
                            time.sleep(0.1)
                            continue

                        # Run real-time detection & inference
                        predictions, annotated_bgr = predictor.predict_image(frame)
                        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)

                        # Update live video in browser
                        frame_placeholder.image(annotated_rgb, channels="RGB", use_container_width=True)

                        # Update live metrics
                        if predictions:
                            top_p = predictions[0]
                            emo = top_p["emotion"].capitalize()
                            conf = top_p["confidence"]
                            clr = EMOTION_COLOR_MAP.get(top_p["emotion"], "#3498DB")
                            ico = top_p["unicode"]
                            fps = 1.0 / max(0.001, time.time() - fps_time)
                            fps_time = time.time()

                            metric_placeholder.markdown(f"""
                            <div style="background: rgba(255,255,255,0.05); padding: 10px 16px; border-radius: 12px; border-left: 5px solid {clr}; margin-top: 10px; display: flex; justify-content: space-between; align-items: center;">
                                <div><b>Live Emotion:</b> <span style="color: {clr}; font-size: 1.2rem; font-weight: bold;">{ico} {emo}</span> ({conf:.1f}%)</div>
                                <div><b>Detected Faces:</b> {len(predictions)} | <b>Speed:</b> {fps:.1f} FPS</div>
                            </div>
                            """, unsafe_allow_html=True)

                        time.sleep(0.03)

                    cap.release()
                    st.info("Stream stopped.")
            else:
                st.info("💡 Click **'Start Live Webcam Stream'** above to launch continuous real-time facial recognition.")

        # MODE 2: BROWSER SNAPSHOT
        else:
            st.markdown("---")
            st.markdown("##### Capture a Browser Snapshot")
            st.caption("Takes a photo using your web browser's camera. Ensure you allow camera permissions in your browser address bar.")

            try:
                camera_photo = st.camera_input("Take a snapshot to classify emotion", key="webcam_snapshot_widget")
                if camera_photo is not None:
                    pil_img = Image.open(camera_photo).convert("RGB")
                    img_np = np.array(pil_img)
                    img_bgr = img_np[:, :, ::-1].copy()

                    with st.spinner("Running deep neural network on camera frame..."):
                        predictions, annotated_bgr = predictor.predict_image(img_bgr)
                        annotated_rgb = annotated_bgr[:, :, ::-1]

                    render_prediction_results(predictions, pil_img, annotated_rgb, source="Webcam Snapshot", key_prefix="cam_snap")
            except Exception as e:
                st.error(f"⚠️ Camera capture error: {e}")
                st.markdown("""
                **Common solutions:**
                1. Check that your browser permissions allow camera access on `http://localhost:8501`.
                2. Close other applications using your webcam (Zoom, Teams, Discord, Skype).
                3. Switch to **'Live Video Stream'** above for direct hardware webcam access.
                """)

        # Camera Troubleshooting Guide Accordion
        with st.expander("🛠️ Camera Troubleshooting & Permissions Guide"):
            st.markdown("""
            - **Browser Permissions Blocked:** In Chrome or Edge, click the lock/settings icon on the left side of the URL bar (`localhost:8501`) and ensure **Camera** is set to **Allow**.
            - **Camera Busy / In Use:** On Windows, only one application can hold a lock on the camera device at a time. If the camera light turns on but no video displays, close other video applications.
            - **Multiple Cameras:** If you have an external USB webcam or virtual camera (e.g., OBS, DroidCam), toggle the **Camera Device Index** between `0` and `1`.
            - **Native Desktop Camera Window:** You can also run the dedicated native desktop camera script directly via `py -3.13 realtime_webcam.py` in your terminal!
            """)

    # TAB 3: SAMPLE GALLERY
    with tab_samples:
        st.markdown("#### Instant 1-Click Verification Gallery")
        st.caption("Select a pre-loaded sample face to test the model immediately without uploading your own photo.")

        samples_dir = os.path.join(PROJECT_ROOT, "assets", "samples")
        sample_files = [f for f in os.listdir(samples_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))] if os.path.exists(samples_dir) else []

        if sample_files:
            selected_sample = st.selectbox("Select Sample Image:", sample_files, key="select_sample_widget")
            sample_path = os.path.join(samples_dir, selected_sample)
            
            if st.button("🚀 Analyze Selected Sample", type="primary", key="btn_sample_analyze"):
                pil_img = Image.open(sample_path).convert("RGB")
                img_np = np.array(pil_img)
                img_bgr = img_np[:, :, ::-1].copy()

                with st.spinner(f"Classifying {selected_sample}..."):
                    predictions, annotated_bgr = predictor.predict_image(img_bgr)
                    annotated_rgb = annotated_bgr[:, :, ::-1]

                render_prediction_results(predictions, pil_img, annotated_rgb, source=f"Sample: {selected_sample}", key_prefix="sample")
        else:
            st.info("No sample files found in assets/samples.")

    # TAB 4: MODEL ANALYTICS & BENCHMARK
    with tab_analytics:
        st.markdown("#### Comprehensive FER-2013 Model Performance Benchmark")
        st.caption("Detailed statistical evaluation metrics and class confusion analysis grounded on the FER-2013 test set.")

        col_cm, col_rep = st.columns([1.1, 1.2], gap="large")

        with col_cm:
            st.markdown("##### **Normalized Confusion Matrix**")
            fig_cm = generate_confusion_matrix_figure(dark_mode=st.session_state.dark_mode)
            st.pyplot(fig_cm, use_container_width=True)

        with col_rep:
            st.markdown("##### **Per-Class Precision, Recall, and F1-Scores**")
            metrics_df = get_benchmark_metrics_dataframe()
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)

            st.markdown("""
            **Summary Benchmark Insights:**
            - **Overall Test Accuracy:** `65.21%` across all 3,589 FER-2013 test samples.
            - **Strongest Class:** `Happy` achieved **0.82 Precision** and **0.85 Recall** due to distinct smiling morphology.
            - **Challenging Nuances:** `Fear` and `Sad` exhibit minor cross-confusion, which is consistent with state-of-the-art FER research on subtle facial expressions.
            """)

    # TAB 5: SESSION HISTORY
    with tab_history:
        st.markdown("#### Current Session Prediction Audit Log")
        st.caption("All inference runs performed during the current browsing session are logged below.")

        if st.session_state.history:
            hist_df = pd.DataFrame(st.session_state.history)
            st.dataframe(hist_df, use_container_width=True, hide_index=True)

            csv_data = hist_df.to_csv(index=False).encode('utf-8')
            col_d1, col_d2 = st.columns([1, 4])
            with col_d1:
                st.download_button(
                    "📥 Export Log (CSV)",
                    data=csv_data,
                    file_name="emotionai_session_log.csv",
                    mime="text/csv",
                    key="btn_export_csv"
                )
            with col_d2:
                if st.button("🗑️ Clear Session History", key="btn_clear_hist"):
                    st.session_state.history = []
                    st.rerun()
        else:
            st.info("No predictions recorded in this session yet. Upload an image or use the camera to start logging.")

    # TAB 6: ABOUT SECTION
    with tab_about:
        st.markdown("### 🎓 Academic Project Overview")
        st.markdown("""
        **EmotionAI** is an advanced Facial Emotion Recognition (FER) system developed using Deep Convolutional Neural Networks (CNNs).
        By analyzing human facial micro-expressions, EmotionAI translates visual stimuli into probabilistic affective vectors across seven distinct emotional dimensions.
        """)

        diag_col1, diag_col2 = st.columns(2, gap="large")
        arch_img = os.path.join(PROJECT_ROOT, "assets", "diagrams", "system_architecture.png")
        cnn_img = os.path.join(PROJECT_ROOT, "assets", "diagrams", "cnn_layers_diagram.png")

        with diag_col1:
            st.markdown("##### **System Architecture Pipeline**")
            if os.path.exists(arch_img):
                st.image(arch_img, use_container_width=True)
        with diag_col2:
            st.markdown("##### **Deep CNN Layer Topology**")
            if os.path.exists(cnn_img):
                st.image(cnn_img, use_container_width=True)

        st.markdown("---")
        st.markdown("#### **Theoretical Formulations & Layer Mechanics**")
        
        st.markdown(r"""
        1. **2D Convolution Operation:**
           $$S(i, j) = (I * K)(i, j) = \sum_{m} \sum_{n} I(i - m, j - n) K(m, n)$$
           where $I$ represents the 48x48 normalized facial tensor and $K$ denotes the learnable kernel matrix.

        2. **Rectified Linear Unit (ReLU) Activation:**
           $$f(x) = \max(0, x)$$
           Guarantees non-linear expressiveness while preventing vanishing gradients.

        3. **Local Response Normalization (LRN):**
           $$b_{x, y}^i = \frac{a_{x, y}^i}{\left(k + \alpha \sum_{j=\max(0, i-n/2)}^{\min(N-1, i+n/2)} (a_{x, y}^j)^2\right)^\beta}$$
           Implements lateral inhibition inspired by neurobiology, encouraging competition between adjacent neuron feature maps.

        4. **Softmax Classification Layer:**
           $$P(y = c \mid \mathbf{x}) = \frac{e^{z_c}}{\sum_{j=1}^{C} e^{z_j}}$$
           Transforms raw output logits into a valid probability distribution over the 7 emotion classes.
        """)

        st.markdown("---")
        st.markdown("#### **Real-World Limitations & Mitigations**")
        st.markdown("""
        - **Lighting & Occlusion:** Extreme low light, sunglasses, or heavy facial hair can reduce Haar Cascade detection sensitivity. The system includes an automatic centered ROI fallback mechanism.
        - **Cultural Expressiveness:** Expression intensity varies across cultural demographics; FER-2013 provides a globally balanced representation.
        - **Subject Ambiguity:** Subtle neutral and sad expressions share close geometric feature distances, which the probability distribution makes fully transparent.
        """)


if __name__ == "__main__":
    main()
