"""
ocr.py
-------------------------------------------------------------------------------
OCR (Optical Character Recognition) abstraction layer.

Real mode: uses pytesseract (a Python wrapper around the open-source
Tesseract OCR engine) if the Tesseract program is installed on the machine.

Mock mode (clearly labeled, never silent): if Tesseract is not installed,
this module returns one of a small set of REALISTIC, CLEARLY-LABELED sample
nutrition-label texts instead of crashing the app. This lets the whole
scanning pipeline (parsing, allergen checking, analysis) be demonstrated
even on a machine without the OCR engine installed. Every result from this
module carries an explicit `mode` field ("real" or "mock") that is shown in
the UI -- the app NEVER pretends a mock result came from a real scan.

To enable real OCR:
    macOS:   brew install tesseract
    Ubuntu:  sudo apt-get install tesseract-ocr
    Windows: https://github.com/UB-Mannheim/tesseract/wiki
Then just run the app again -- no code changes needed.
-------------------------------------------------------------------------------
"""

import random
from dataclasses import dataclass

import numpy as np

from src.utils import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import pytesseract
    if config.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
    PYTESSERACT_IMPORTED = True
except ImportError:
    PYTESSERACT_IMPORTED = False


@dataclass
class OCRResult:
    text: str
    confidence: float   # 0.0 - 1.0
    mode: str            # "real" or "mock"


# --------------------------------------------------------------------------
# Sample label texts used ONLY in mock mode, clearly labeled as synthetic
# demo text representing what a real nutrition label commonly looks like.
# These let the parser, allergen-checker, and analysis engine be
# demonstrated end-to-end without a real OCR engine installed.
# --------------------------------------------------------------------------
_MOCK_LABEL_SAMPLES = [
    """Nutrition Facts
Serving Size 40g
Calories 190
Total Fat 8g
Saturated Fat 3.5g
Sodium 210mg
Total Carbohydrate 25g
Dietary Fiber 2g
Sugars 12g
Protein 4g
Ingredients: Wheat flour, sugar, palm oil, cocoa solids, milk solids,
peanut, salt, raising agents, emulsifiers (soy lecithin), artificial flavour.
""",
    """NUTRITION INFORMATION
Serving size: 30g
Energy 160 kcal
Protein 20g
Carbohydrate 6g
of which sugars 2g
Fat 5g
of which saturates 2g
Sodium 150mg
Ingredients: Whey protein concentrate, soy protein isolate, cocoa powder,
almond pieces, natural flavours, sucralose.
""",
]


def is_real_ocr_available() -> bool:
    if not PYTESSERACT_IMPORTED:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def run_ocr(image: np.ndarray) -> OCRResult:
    """
    Run OCR on a preprocessed image (see image_preprocessor.py). Falls back
    to a clearly-labeled mock result if Tesseract is unavailable.
    """
    if is_real_ocr_available():
        try:
            text = pytesseract.image_to_string(image)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and int(c) >= 0]
            avg_confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0
            return OCRResult(text=text.strip(), confidence=round(avg_confidence, 3), mode="real")
        except Exception as exc:
            logger.warning("Real OCR failed (%s); falling back to mock mode.", exc)

    sample_text = random.choice(_MOCK_LABEL_SAMPLES)
    logger.info("Tesseract OCR engine not available -- returning a labeled MOCK OCR result.")
    return OCRResult(text=sample_text.strip(), confidence=0.55, mode="mock")
