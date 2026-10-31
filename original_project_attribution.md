# Original Project Attribution and Heritage

## Upstream Repository Details
- **Original Project Name:** Facial Expression Recognition (FER)
- **Original Author:** xionghc
- **Original GitHub Repository:** [https://github.com/xionghc/Facial-Expression-Recognition](https://github.com/xionghc/Facial-Expression-Recognition)
- **Original License:** MIT License

---

## Architectural Heritage & Original Foundations
The original project provided:
1. A foundational Deep CNN model (`deepnn`) written in legacy TensorFlow 1.1.0 graph execution syntax.
2. A trained checkpoint file (`ckpt/emotion_model-30001`) achieving approximately 65% test accuracy on the Kaggle FER-2013 dataset.
3. A basic desktop script (`demo.py`) that used OpenCV desktop GUI (`cv2.imshow` and `cv2.waitKey(' ')`) to capture single frames via local webcam.
4. Emoji icon assets corresponding to 7 emotion categories.

---

## Major Transformations, Modernization, and Customizations Implemented

The project has been completely refactored and transformed into **EmotionAI**, an academic-grade, deployable affective computing application:

1. **Modern Deep Learning Engine:**
   - Eliminated deprecated TensorFlow 1.x dependencies (`tf.Session`, `tf.placeholder`, `tf.train.Saver`, `tf.truncated_normal`, `tf.app.flags`).
   - Implemented dual-backend architecture: modern TensorFlow 2.x Eager graph execution (`@tf.function`) combined with a standalone, ultra-fast Vectorized NumPy engine for instant CPU inference.
   - Extracted and preserved 100% of the trained parameters into a lightweight, portable compressed archive (`model_weights.npz`, 13.5 MB) while keeping original checkpoint assets intact.

2. **Clean Modular Architecture (`src/`):**
   - `src/preprocessing.py`: Multi-scale face detection, bicubic interpolation, multi-face extraction, contrast equalization, and aesthetic bounding-box rendering with corner markers.
   - `src/prediction.py`: Thread-safe `EmotionPredictor` with singleton caching, multi-face classification, sorted confidence scoring, and emoji resolution.
   - `src/utils.py`: Affective radar diagrams, probability distributions, FER-2013 confusion matrix heatmaps, classification performance metrics, and session audit tracking.
   - `src/generate_diagrams.py`: High-resolution diagram synthesis for publication and reporting.

3. **Enterprise-Grade Web Application (`app.py`):**
   - Built with Streamlit featuring a responsive AI dashboard interface, glassmorphic metric cards, dark/light theme switching, and multi-face selection.
   - Multi-modal input support: Image upload (JPG/PNG), instant browser camera snapshots via `st.camera_input`, and an interactive 1-click sample gallery.
   - Full confidence breakdowns with interactive bar charts, radar profiles, and downloadable session history (CSV).

4. **Deployment & Submission Packaging:**
   - Pre-configured for seamless 1-click deployment on Streamlit Community Cloud and cloud container environments (`requirements.txt`, `packages.txt`).
   - Comprehensive university-standard Academic Project Report provided in both DOCX and PDF formats.

---
*Maintained under the MIT License in full compliance with original open-source terms.*
