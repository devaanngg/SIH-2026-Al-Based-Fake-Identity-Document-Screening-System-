from typing import Dict, Any, List
from app.models.schemas import TamperingResult, ValidationResult, FaceMatchResult, RiskAssessment


class RiskScorer:
    """Calculate overall risk score based on multiple detection modules."""
    
    def __init__(self):
        # Risk level thresholds
        self.thresholds = {
            "low": 30,
            "medium": 60,
            "high": 80,
            "critical": 100
        }
    
    def calculate_risk(self, tampering: TamperingResult, validation: ValidationResult,
                       face_match: FaceMatchResult) -> RiskAssessment:
        """Calculate combined risk score."""
        
        # Tampering contribution (0-100)
        tampering_weight = 0.4
        tampering_contribution = tampering.score * tampering_weight
        tampering_factors = []
        
        if tampering.has_tampering:
            tampering_factors.append(f"Tampering detected (score: {tampering.score:.1f})")
            for key, details in tampering.details.items():
                if isinstance(details, dict) and any(
                    details.get(k, 0) for k in ["high_error_percentage", "suspicious_regions", "suspicious_matches"]
                ):
                    tampering_factors.append(f"  - {key.replace('_', ' ').title()}: suspicious patterns")
        
        # Validation contribution (0-100)
        validation_weight = 0.3
        if validation.is_valid:
            validation_score = 5  # Low risk when valid
            validation_factors = []
        else:
            validation_score = min(100, 30 + len(validation.errors) * 20)
            validation_factors = [f"Validation failed: {'; '.join(validation.errors[:3])}"]
        
        validation_contribution = validation_score * validation_weight
        
        # Face match contribution
        face_weight = 0.3
        if face_match.match:
            face_score = 5  # Low risk when faces match
            face_factors = [f"Face matched (similarity: {face_match.score:.1f}%)"]
        else:
            face_score = 80  # High risk when faces don't match
            face_factors = [f"Face verification failed (similarity: {face_match.score:.1f}%)"]
        
        face_contribution = face_score * face_weight
        
        # Additional factors
        warning_factors = [f"Warning: {w}" for w in validation.warnings]
        
        # Calculate final score
        risk_score = tampering_contribution + validation_contribution + face_contribution
        
        # Clamp to 0-100
        risk_score = max(0, min(100, risk_score))
        
        # Determine risk level
        if risk_score < 30:
            risk_level = "low"
        elif risk_score < 60:
            risk_level = "medium"
        elif risk_score < 80:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        # Compile all factors
        all_factors = tampering_factors + validation_factors + face_factors + warning_factors
        
        return RiskAssessment(
            risk_score=round(risk_score, 2),
            risk_level=risk_level,
            factors=all_factors
        )


risk_scorer = RiskScorer()
