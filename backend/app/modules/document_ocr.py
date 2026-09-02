"""Document OCR extraction using RapidOCR (ONNX PaddleOCR) with fallbacks.

Module 1: Extract all relevant fields from identity documents.

Backends tried in order:
1. RapidOCR - ONNX Runtime port of PaddleOCR (lightweight, no paddlepaddle needed)
2. EasyOCR - PyTorch-based, strong multilingual support
3. pytesseract - lightest, requires Tesseract binary

Each backend is optional; the extractor degrades gracefully.
"""
import cv2
import numpy as np
import re
from typing import Dict, List, Optional
from app.models.schemas import OCRData
from app.modules.mrz_parser import mrz_parser


class DocumentOCRExtractor:
    """High-accuracy OCR extraction for identity documents."""

    def __init__(self):
        self._rapid = None
        self._easy = None
        self._tesseract_available = None

    # ------------------------------------------------------------------
    # Backend initialization (lazy)
    # ------------------------------------------------------------------
    def _get_rapid(self):
        if self._rapid is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                self._rapid = RapidOCR()
            except ImportError:
                self._rapid = False
        return self._rapid or None

    def _get_easy(self):
        if self._easy is None:
            try:
                import easyocr
                self._easy = easyocr.Reader(['en'], gpu=False, verbose=False)
            except ImportError:
                self._easy = False
        return self._easy or None

    def _tesseract_ready(self):
        if self._tesseract_available is None:
            try:
                import pytesseract
                pytesseract.get_tesseract_version()
                self._tesseract_available = True
            except Exception:
                self._tesseract_available = False
        return self._tesseract_available

    # ------------------------------------------------------------------
    # Core recognition methods
    # ------------------------------------------------------------------
    def recognize(self, image: np.ndarray) -> List[Dict]:
        """Run best-available OCR backend and return list of {text, confidence, box}."""
        # Try RapidOCR first
        rapid = self._get_rapid()
        if rapid:
            try:
                result, _ = rapid(image)
                if result:
                    return [
                        {"text": r[1], "confidence": float(r[2]), "box": r[0]}
                        for r in result
                    ]
            except Exception:
                pass

        # Try EasyOCR
        easy = self._get_easy()
        if easy:
            try:
                result = easy.readtext(image)
                if result:
                    return [
                        {"text": r[1], "confidence": float(r[2]), "box": r[0]}
                        for r in result
                    ]
            except Exception:
                pass

        # Fallback to tesseract
        if self._tesseract_ready():
            try:
                import pytesseract
                processed = self._preprocess(image)
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(processed, config=custom_config)
                return [
                    {"text": line, "confidence": 70.0, "box": None}
                    for line in text.split('\n') if line.strip()
                ]
            except Exception:
                pass

        return []

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Enhance document image for better OCR."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        return binary

    # ------------------------------------------------------------------
    # Field extraction
    # ------------------------------------------------------------------
    def _extract_fields(self, text: str, document_type: str) -> Dict[str, str]:
        """Regex-based field extraction from raw OCR text.

        Regex extraction from the human-readable fields is the primary
        source, since it reads clean document labels reliably. MRZ parsing
        is used separately as a cross-check / for MRZ-only documents.
        """
        fields: Dict[str, str] = {}

        # Date patterns (with knowledge of which is DOB vs expiry based on label)
        date_pattern = r"\d{2}[./-]\d{2}[./-]\d{2,4}"

        name_match = re.search(
            r"(?:\bName\s*[\.:]\s*)([A-Z][A-Z\s]{1,40})(?:\n|$)", text, re.IGNORECASE
        )
        if name_match:
            name = name_match.group(1).strip()
            # Reject if it looks like MRZ garbage (contains < or many punctuation)
            if "<" not in name and name.count("\n") == 0:
                fields["name"] = name

        surname_match = re.search(
            r"(?:SURNAME|Last[ ]?Name)\s*[\.:]\s*([A-Z][A-Z\s]{1,30})", text, re.IGNORECASE
        )
        if surname_match:
            fields["surname"] = surname_match.group(1).strip()

        given_match = re.search(
            r"(?:GIVEN[ ]?NAMES?|First[ ]?Name)\s*[\.:]\s*([A-Z][A-Z\s]{1,30})", text, re.IGNORECASE
        )
        if given_match:
            fields["given_name"] = given_match.group(1).strip()

        # Passport / document number: allow digits and a leading letter
        pnum = re.search(
            r"(?:Passport\s*(?:No|Number|#)?\s*[\.:]\s*)([A-Z]{0,2}\d{5,15})", text, re.IGNORECASE
        )
        if pnum:
            fields["passport_number"] = pnum.group(1).strip()

        dnum = re.search(
            r"(?:Document\s*(?:No|Number|#)?|ID\s*[\.:]?\s*|No\s*[\.:])\s*([A-Z0-9]{5,20})",
            text, re.IGNORECASE,
        )
        if dnum:
            fields["document_number"] = dnum.group(1).strip()

        nat = re.search(
            r"(?:Nationality|NATIONALITY)\s*[\.:]\s*([A-Z]{2,3})", text, re.IGNORECASE
        )
        if nat and "<" not in nat.group(1):
            fields["nationality"] = nat.group(1).strip()

        gender = re.search(
            r"\b(Sex|Gender|GENDER)\s*[\.:]\s*([MF])", text, re.IGNORECASE
        )
        if gender:
            fields["gender"] = gender.group(2).strip()

        dob = re.search(
            r"(?:Date\s*of\s*Birth|DOB)\s*[\.:]\s*(\d{2}[./-]\d{2}[./-]\d{2,4})",
            text, re.IGNORECASE,
        )
        if dob:
            fields["date_of_birth"] = dob.group(1).strip()

        exp = re.search(
            r"(?:Date\s*of\s*Expiry|Expiry\s*\.?\s*Date|EXPIRY)\s*[\.:]\s*(\d{2}[./-]\d{2}[./-]\d{2,4})",
            text, re.IGNORECASE,
        )
        if exp:
            fields["date_of_expiry"] = exp.group(1).strip()

        visa_no = re.search(
            r"Visa\s*(?:No|Number|#)?\s*[\.:]\s*([A-Z0-9]{4,20})", text, re.IGNORECASE
        )
        if visa_no:
            fields["visa_number"] = visa_no.group(1).strip()

        visa_type = re.search(
            r"(?:Visa\s*Type|Type)\s*[\.:]\s*([A-Z]{2,10})", text, re.IGNORECASE
        )
        if visa_type:
            fields["visa_type"] = visa_type.group(1).strip()

        # Fill document_number from passport_number if not independently found
        if "passport_number" in fields and "document_number" not in fields:
            fields["document_number"] = fields["passport_number"]

        return fields

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def _apply_mrz(self, ocr_data: OCRData, mrz) -> None:
        """Apply MRZ fields only when MRZ parsed with a confident result.

        MRZ is authoritative for machine-readable fields (number, DOB, expiry,
        gender, nationality). To avoid corrupting cleanly-extracted regex
        fields with a mis-detected MRZ, each MRZ value is only applied when it
        looks well-formed (no '<' filler, plausible length).
        """
        if not mrz or not mrz.document_type:
            return

        def clean(value: str) -> bool:
            return bool(value) and "<" not in value and len(value) >= 2

        if clean(mrz.document_number):
            ocr_data.passport_number = mrz.document_number
            ocr_data.document_number = mrz.document_number
        if clean(mrz.country_code) and mrz.country_code.isalpha():
            ocr_data.nationality = mrz.country_code
        if clean(mrz.date_of_birth):
            ocr_data.date_of_birth = mrz.date_of_birth
        if clean(mrz.expiry_date):
            ocr_data.date_of_expiry = mrz.expiry_date
        if mrz.sex and mrz.sex in ("M", "F"):
            ocr_data.gender = mrz.sex
        # Only use MRZ name if regex didn't extract a clean one
        if not ocr_data.name and (mrz.first_name or mrz.last_name):
            ocr_data.name = " ".join(
                filter(None, [mrz.first_name, mrz.last_name])
            ) or None
        ocr_data.mrz_valid = mrz.is_valid
        ocr_data.mrz_data = {
            "format": mrz.format_type,
            "document_type": mrz.document_type,
            "country_code": mrz.country_code,
            "document_number": mrz.document_number,
            "date_of_birth": mrz.date_of_birth,
            "date_of_expiry": mrz.expiry_date,
            "sex": mrz.sex,
            "checksums": mrz.checksums,
            "errors": mrz.errors,
            "is_valid": mrz.is_valid,
        }

    def process_document(self, image_path: str, document_type: str) -> OCRData:
        """Process a document image through OCR + MRZ parsing."""
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Run OCR
        ocr_items = self.recognize(image)
        full_text = "\n".join(item["text"] for item in ocr_items if item["text"])

        ocr_data = OCRData(raw_text=full_text or None)

        # 1. Regex-based field extraction from human-readable fields (primary)
        fields = self._extract_fields(full_text, document_type)
        for key, value in fields.items():
            if hasattr(ocr_data, key) and value is not None:
                setattr(ocr_data, key, value)

        # 2. MRZ parsing as cross-check / authoritative source when present
        mrz = None
        if full_text:
            mrz = mrz_parser.from_text(full_text)
            self._apply_mrz(ocr_data, mrz)

        return ocr_data

    def extract_mrz(self, text: str):
        """Expose MRZ parsing for downstream checksum validation."""
        return mrz_parser.from_text(text)


document_ocr = DocumentOCRExtractor()
