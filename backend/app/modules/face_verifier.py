"""Face verification using InsightFace (ArcFace) with OpenCV fallback.

Module 4: Ensure document owner matches the presented individual.

Primary: InsightFace (buffalo_l) for high-accuracy face embeddings.
Fallback: OpenCV-based face detection + correlation comparison.
"""
import cv2
import numpy as np
import os
from typing import Optional, Tuple
from app.models.schemas import FaceMatchResult


class FaceVerifier:
    """Verify document owner matches presented individual."""

    def __init__(self):
        self._insight = None
        self.face_cascade = None

        # Load Haar cascade as fallback detector
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(cascade_path):
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
        except Exception:
            self.face_cascade = None

    # ------------------------------------------------------------------
    def _get_insight(self):
        """Lazy-load InsightFace FaceAnalysis model."""
        if self._insight is None:
            try:
                from insightface.app import FaceAnalysis
                from insightface.model_zoo import get_model
                app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
                app.prepare(ctx_id=0, det_size=(640, 640))
                self._insight = app
            except Exception:
                self._insight = False
        return self._insight or None

    def _detect_haar(self, image):
        if self.face_cascade is not None:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
            )
            if len(faces) > 0:
                return faces
        return []

    # ------------------------------------------------------------------
    def extract_face(self, image_path: str) -> Optional[dict]:
        """Extract face info from image. Returns dict with 'image' crop and 'embedding'."""
        image = cv2.imread(image_path)
        if image is None:
            return None

        # Try InsightFace first
        insight = self._get_insight()
        if insight:
            try:
                faces = insight.get(image)
                if faces and len(faces) > 0:
                    # Pick largest face
                    largest = max(faces, key=lambda f: f.bbox[2] * f.bbox[3])
                    x1, y1, x2, y2 = [int(v) for v in largest.bbox]
                    crop = image[y1:y2, x1:x2]
                    return {
                        "crop": crop,
                        "embedding": largest.normed_embedding,
                        "detection": "insightface",
                        "bbox": (x1, y1, x2 - x1, y2 - (y1))
                    }
            except Exception:
                pass

        # Fallback: Haar detection + correlation features
        faces = self._detect_haar(image)
        if len(faces) == 0:
            return None

        largest = max(faces, key=lambda f: f[2] * f[3])
        x, y, fw, fh = largest
        crop = image[y:y+fh, x:x+fw]
        return {
            "crop": crop,
            "embedding": self._fallback_embedding(crop),
            "detection": "haar",
            "bbox": (x, y, fw, fh)
        }

    def _fallback_embedding(self, crop: np.ndarray) -> np.ndarray:
        """Compute a simple perceptual feature vector as embedding fallback."""
        try:
            resized = cv2.resize(crop, (64, 64))
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            hog = cv2.HOGDescriptor((64, 64), (16, 16), (8, 8), (8, 8)).compute(gray)
            return hog / (np.linalg.norm(hog) + 1e-8)
        except Exception:
            return None

    # ------------------------------------------------------------------
    def compare_faces(self, face_a: Optional[dict], face_b: Optional[dict]) -> Tuple[float, bool]:
        """Compare two face descriptors. Returns (similarity, is_match)."""
        if not face_a or not face_b:
            return 0.0, False

        emb_a = face_a.get("embedding")
        emb_b = face_b.get("embedding")

        if emb_a is not None and emb_b is not None:
            try:
                # Cosine similarity
                sim = float(np.dot(emb_a, emb_b) / (
                    np.linalg.norm(emb_a) * np.linalg.norm(emb_b) + 1e-8
                ))
                # Convert cosine sim in [-1,1] to 0-100
                score = max(0.0, min(100.0, (sim + 1) / 2 * 100))
                return score, score >= 65
            except Exception:
                pass

        # Fallback: raw correlation on crops
        if face_a.get("crop") is not None and face_b.get("crop") is not None:
            try:
                g1 = cv2.cvtColor(cv2.resize(face_a["crop"], (128, 128)), cv2.COLOR_BGR2GRAY)
                g2 = cv2.cvtColor(cv2.resize(face_b["crop"], (128, 128)), cv2.COLOR_BGR2GRAY)
                g1 = (g1 - np.mean(g1)) / (np.std(g1) + 1e-8)
                g2 = (g2 - np.mean(g2)) / (np.std(g2) + 1e-8)
                corr = np.corrcoef(g1.flatten(), g2.flatten())[0, 1]
                score = max(0.0, corr * 100)
                return score, score >= 55
            except Exception:
                pass

        return 0.0, False

    def get_crop(self, image_path: str) -> Optional[np.ndarray]:
        """Return the face crop for a document image (for photo replacement checks)."""
        face = self.extract_face(image_path)
        if face:
            return face.get("crop")
        return None

    def verify_faces(self, document_path: str, live_path: str) -> FaceMatchResult:
        """Compare document photo with live capture."""
        doc_face = self.extract_face(document_path)
        live_face = self.extract_face(live_path)

        if doc_face is None or live_face is None:
            return FaceMatchResult(score=0.0, match=False, confidence=0.0)

        score, is_match = self.compare_faces(doc_face, live_face)

        return FaceMatchResult(
            score=round(score, 2),
            match=is_match,
            confidence=round(min(100.0, score + 10), 2)
        )


face_verifier = FaceVerifier()
