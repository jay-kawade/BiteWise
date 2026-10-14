"""
image_preprocessor.py
-------------------------------------------------------------------------------
Cleans up a photo of a nutrition label BEFORE it is sent to OCR. OCR engines
like Tesseract read clean, high-contrast, upright black-on-white text far
more reliably than a raw photo with shadows, glare, or a skewed angle.

Steps applied (standard, well-known OpenCV techniques -- not invented):
    1. Convert to grayscale        -- OCR only needs light/dark, not color.
    2. Denoise                     -- reduces camera sensor noise/grain.
    3. Adaptive thresholding       -- converts to pure black/white text,
                                       adapting to uneven lighting across
                                       the label (better than one global
                                       threshold for a photographed label).
    4. Mild dilation                -- thickens thin text strokes slightly,
                                       which helps Tesseract on low-resolution
                                       photos.

If OpenCV is not installed, `preprocess_image` returns the original image
unchanged and flags that preprocessing was skipped -- the app must not crash
just because an optional image-processing dependency is missing.
-------------------------------------------------------------------------------
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


@dataclass
class PreprocessResult:
    image: np.ndarray
    preprocessing_applied: bool
    note: str = ""


def preprocess_image(image: np.ndarray) -> PreprocessResult:
    """
    `image` is expected to be a numpy array in BGR or grayscale format (the
    format OpenCV and Streamlit's image widgets both use). Returns a
    PreprocessResult with a cleaned-up grayscale/binary image ready for OCR.
    """
    if not OPENCV_AVAILABLE:
        return PreprocessResult(
            image=image,
            preprocessing_applied=False,
            note="OpenCV is not installed; using the original image without cleanup. "
                 "OCR accuracy may be lower on noisy/angled photos.",
        )

    if image is None or image.size == 0:
        raise ValueError("Received an empty image.")

    # Step 1: grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Step 2: denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Step 3: adaptive threshold -> clean black/white text
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )

    # Step 4: mild dilation to thicken thin strokes
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.dilate(binary, kernel, iterations=1)

    return PreprocessResult(image=processed, preprocessing_applied=True)


def decode_image_bytes(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Decode raw uploaded image bytes (e.g. from Streamlit's file_uploader)
    into an OpenCV image. Returns None if there are no bytes to decode or
    decoding fails -- the caller (scanner_service.py) treats that as "no
    image available" and proceeds in OCR mock mode rather than crashing.
    """
    if not OPENCV_AVAILABLE or not image_bytes:
        return None
    try:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return image
    except Exception:
        return None
