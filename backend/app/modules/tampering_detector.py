import cv2
import numpy as np
from scipy import ndimage
from skimage import feature, measure
from typing import Dict, Any, Tuple
import math
from app.models.schemas import TamperingResult


class TamperingDetector:
    """Module 3: Detect digitally or physically altered documents using AI."""
    
    def __init__(self):
        self.error_level_threshold = 15.0
        self.noise_threshold = 30.0
        self.copy_move_threshold = 0.95
    
    def analyze_error_level(self, image: np.ndarray) -> Tuple[float, Dict[str, Any]]:
        """Error Level Analysis (ELA) - detects digital manipulations."""
        # Convert to RGB if needed
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        # Save and reload at known quality
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, 95]
        _, buffer = cv2.imencode('.jpg', image, encode_params)
        resaved = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        
        # Calculate difference
        diff = cv2.absdiff(image, resaved)
        
        # Convert to grayscale
        if len(diff.shape) == 3:
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        else:
            diff_gray = diff
        
        # Calculate statistics
        mean_error = np.mean(diff_gray)
        max_error = np.max(diff_gray)
        std_error = np.std(diff_gray)
        
        # Find regions with high error levels
        _, high_error_mask = cv2.threshold(diff_gray, self.error_level_threshold, 255, cv2.THRESH_BINARY)
        high_error_percentage = np.sum(high_error_mask > 0) / high_error_mask.size * 100
        
        details = {
            "mean_error_level": float(mean_error),
            "max_error_level": float(max_error),
            "std_error_level": float(std_error),
            "high_error_percentage": float(high_error_percentage),
            "suspicious_regions": int(np.sum(high_error_mask > 0) // 1000)
        }
        
        # Score: higher error level = more likely tampering
        score = min(100, (mean_error * 2 + high_error_percentage * 3) / 5)
        
        return score, details
    
    def analyze_noise_distribution(self, image: np.ndarray) -> Tuple[float, Dict[str, Any]]:
        """Detect inconsistencies in noise patterns."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply noise extraction using high-pass filter
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        noise = cv2.subtract(gray, blurred)
        
        # Divide into blocks and analyze noise variance
        h, w = noise.shape
        block_size = 64
        noise_variances = []
        
        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = noise[y:y+block_size, x:x+block_size]
                variance = np.var(block)
                noise_variances.append(variance)
        
        if not noise_variances:
            return 0, {"message": "Image too small for noise analysis"}
        
        mean_variance = np.mean(noise_variances)
        std_variance = np.std(noise_variances)
        
        # Detect blocks with significantly different noise
        threshold = mean_variance + 2 * std_variance
        inconsistent_blocks = sum(1 for v in noise_variances if abs(v - mean_variance) > threshold)
        inconsistency_ratio = inconsistent_blocks / len(noise_variances)
        
        details = {
            "mean_noise_variance": float(mean_variance),
            "noise_inconsistency": float(inconsistency_ratio),
            "inconsistent_blocks": inconsistent_blocks,
            "total_blocks": len(noise_variances)
        }
        
        score = min(100, inconsistency_ratio * 200)
        
        return score, details
    
    def detect_copy_move(self, image: np.ndarray) -> Tuple[float, Dict[str, Any]]:
        """Detect copy-move forgery using feature matching."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Detect features using ORB
        orb = cv2.ORB_create(nfeatures=1000)
        keypoints, descriptors = orb.detectAndCompute(gray, None)
        
        if descriptors is None or len(keypoints) < 10:
            return 0, {"message": "Insufficient features detected"}
        
        # Match features
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(descriptors, descriptors)
        
        # Filter self-matches and find similar regions
        good_matches = []
        for m in matches:
            if m.queryIdx != m.trainIdx:
                # Check if keypoints are far apart (potential copy-move)
                pt1 = keypoints[m.queryIdx].pt
                pt2 = keypoints[m.trainIdx].pt
                distance = math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                
                if distance > 50:  # Minimum distance between copied regions
                    if m.distance < 50:  # Good match quality
                        good_matches.append(m)
        
        # Calculate score
        match_ratio = len(good_matches) / len(keypoints) if keypoints else 0
        score = min(100, match_ratio * 500)
        
        details = {
            "total_keypoints": len(keypoints),
            "total_matches": len(matches),
            "suspicious_matches": len(good_matches),
            "match_ratio": float(match_ratio)
        }
        
        return score, details
    
    def detect_edge_inconsistencies(self, image: np.ndarray) -> Tuple[float, Dict[str, Any]]:
        """Detect unnatural edges that may indicate splicing."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyze contour properties
        edge_scores = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Filter small contours
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * math.pi * area / (perimeter ** 2)
                    edge_scores.append(circularity)
        
        if not edge_scores:
            return 0, {"message": "No significant edges detected"}
        
        mean_circularity = np.mean(edge_scores)
        std_circularity = np.std(edge_scores)
        
        # Unnatural edges often have very regular shapes
        unnatural_count = sum(1 for s in edge_scores if s > 0.8)
        unnatural_ratio = unnatural_count / len(edge_scores)
        
        details = {
            "total_contours": len(contours),
            "mean_circularity": float(mean_circularity),
            "unnatural_edges": unnatural_count,
            "unnatural_ratio": float(unnatural_ratio)
        }
        
        score = min(100, unnatural_ratio * 150)
        
        return score, details
    
    def detect_stamp_anomalies(self, image: np.ndarray) -> Tuple[float, Dict[str, Any]]:
        """Detect forged or tampered stamps."""
        if len(image.shape) == 3:
            # Look for stamp-like colors (blue, red, purple)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Blue stamp mask
            lower_blue = np.array([100, 50, 50])
            upper_blue = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            # Red stamp mask
            lower_red1 = np.array([0, 50, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 50, 50])
            upper_red2 = np.array([180, 255, 255])
            red_mask = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)
            
            stamp_mask = blue_mask | red_mask
        else:
            return 0, {"message": "Stamp detection requires color image"}
        
        # Analyze stamp regions
        contours, _ = cv2.findContours(stamp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        stamp_info = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Minimum stamp size
                x, y, w, h = cv2.boundingRect(contour)
                roi = stamp_mask[y:y+h, x:x+w]
                
                # Analyze stamp density and uniformity
                density = np.sum(roi > 0) / roi.size
                stamp_info.append({
                    "area": int(area),
                    "density": float(density),
                    "position": (int(x), int(y))
                })
        
        # Check for stamp anomalies
        anomaly_score = 0
        if stamp_info:
            densities = [s["density"] for s in stamp_info]
            if len(densities) > 1:
                density_std = np.std(densities)
                if density_std > 0.2:  # High variation in stamp density
                    anomaly_score += 30
        
        details = {
            "stamps_detected": len(stamp_info),
            "stamp_info": stamp_info[:5],  # Limit output
            "anomaly_score": float(anomaly_score)
        }
        
        return min(100, anomaly_score), details
    
    def analyze_metadata(self, image_path: str) -> Tuple[float, Dict[str, Any]]:
        """Analyze image metadata for signs of editing."""
        import os
        
        details = {
            "file_size": os.path.getsize(image_path),
            "has_exif": False,
            "editing_software": None,
            "metadata_anomalies": []
        }
        
        score = 0
        
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            img = Image.open(image_path)
            
            if hasattr(img, '_getexif') and img._getexif():
                details["has_exif"] = True
                exif_data = img._getexif()
                
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    # Check for editing software
                    if tag in ["Software", "ProcessingSoftware", "HostComputer"]:
                        details["editing_software"] = str(value)
                        editing_keywords = ["photoshop", "gimp", "lightroom", "paint", "edit"]
                        if any(kw in str(value).lower() for kw in editing_keywords):
                            score += 40
                            details["metadata_anomalies"].append(f"Editing software detected: {value}")
                    
                    # Check for modification date
                    if tag == "DateTimeOriginal":
                        details["original_date"] = str(value)
                    
                    if tag == "DateTimeModified":
                        details["modified_date"] = str(value)
                        if details.get("original_date") and value != details["original_date"]:
                            score += 20
                            details["metadata_anomalies"].append("Creation and modification dates differ")
        
        except Exception as e:
            details["metadata_error"] = str(e)
        
        return min(100, score), details
    
    def detect_tampering(self, image_path: str) -> TamperingResult:
        """Main tampering detection pipeline."""
        image = cv2.imread(image_path)
        if image is None:
            return TamperingResult(
                score=0,
                has_tampering=False,
                details={"error": "Could not load image"}
            )
        
        all_details = {}
        scores = []
        
        # 1. Error Level Analysis
        ela_score, ela_details = self.analyze_error_level(image)
        scores.append(ela_score)
        all_details["error_level_analysis"] = ela_details
        
        # 2. Noise Distribution Analysis
        noise_score, noise_details = self.analyze_noise_distribution(image)
        scores.append(noise_score)
        all_details["noise_analysis"] = noise_details
        
        # 3. Copy-Move Detection
        copy_score, copy_details = self.detect_copy_move(image)
        scores.append(copy_score)
        all_details["copy_move_detection"] = copy_details
        
        # 4. Edge Inconsistency Detection
        edge_score, edge_details = self.detect_edge_inconsistencies(image)
        scores.append(edge_score)
        all_details["edge_analysis"] = edge_details
        
        # 5. Stamp Anomaly Detection
        stamp_score, stamp_details = self.detect_stamp_anomalies(image)
        scores.append(stamp_score)
        all_details["stamp_analysis"] = stamp_details
        
        # 6. Metadata Analysis
        meta_score, meta_details = self.analyze_metadata(image_path)
        scores.append(meta_score)
        all_details["metadata_analysis"] = meta_details
        
        # Calculate weighted average score
        weights = [0.25, 0.15, 0.2, 0.15, 0.1, 0.15]
        final_score = sum(s * w for s, w in zip(scores, weights))
        
        return TamperingResult(
            score=round(final_score, 2),
            has_tampering=final_score > 40,
            details=all_details
        )


tampering_detector = TamperingDetector()
