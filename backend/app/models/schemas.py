from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    status: str
    message: str


class OCRData(BaseModel):
    name: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    date_of_expiry: Optional[str] = None
    gender: Optional[str] = None
    visa_number: Optional[str] = None
    visa_type: Optional[str] = None
    entry_validation: Optional[str] = None
    stay_duration: Optional[str] = None
    document_number: Optional[str] = None
    issue_date: Optional[str] = None
    raw_text: Optional[str] = None
    mrz_valid: Optional[bool] = None
    mrz_data: Optional[dict] = None


class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class TamperingResult(BaseModel):
    score: float
    has_tampering: bool
    details: Dict[str, Any]


class FaceMatchResult(BaseModel):
    score: float
    match: bool
    confidence: float


class RiskAssessment(BaseModel):
    risk_score: float
    risk_level: str  # low, medium, high, critical
    factors: List[str]


class ScreeningResult(BaseModel):
    document_id: int
    document_type: str
    ocr_data: OCRData
    validation: ValidationResult
    tampering: TamperingResult
    face_match: FaceMatchResult
    risk_assessment: RiskAssessment
    status: str
    processed_at: datetime


class DocumentRecordResponse(BaseModel):
    id: int
    document_type: str
    filename: str
    upload_time: datetime
    extracted_data: Optional[Dict] = None
    is_valid: bool
    validation_errors: Optional[List] = None
    tampering_score: float
    has_tampering: bool
    face_match_score: float
    face_match: bool
    risk_score: float
    risk_level: Optional[str] = None
    status: str
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_documents: int
    flagged_documents: int
    high_risk_count: int
    average_processing_time: float
    documents_by_type: Dict[str, int]
    risk_distribution: Dict[str, int]
