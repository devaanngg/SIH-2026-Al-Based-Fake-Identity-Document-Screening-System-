import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
import logging

from app.database import get_db
from app.models.schemas import (
    DocumentUploadResponse, ScreeningResult, DocumentRecordResponse, DashboardStats
)
from app.modules.document_ocr import document_ocr
from app.modules.document_validator import document_validator
from app.modules.tampering_detector import tampering_detector
from app.modules.face_verifier import face_verifier
from app.services.risk_scorer import risk_scorer

router = APIRouter(prefix="/api", tags=["screening"])
logger = logging.getLogger(__name__)

VALID_DOCUMENT_TYPES = ["passport", "visa", "national_id", "driving_license"]


def save_upload_file(upload: UploadFile) -> tuple[str, str]:
    """Save uploaded file and return path and original filename."""
    # Create upload directory if not exists
    os.makedirs("uploads", exist_ok=True)
    
    # Generate unique filename
    ext = os.path.splitext(upload.filename or "")[1].lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Supported image formats: JPG, PNG, WEBP")
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join("uploads", unique_name)
    
    # Save file
    content = upload.file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    return file_path, upload.filename or unique_name


def process_document_records(document_id: int):
    """Background task to process document with all modules."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        record = db.query(type("Doc", (), {})).filter(type("Doc", (), {}).id == document_id).first()
    except Exception:
        pass
    finally:
        db.close()


@router.post("/screening/documents", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    document_type: str,
    file: UploadFile = File(...),
    live_photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Upload and screen a document."""
    
    # Validate document type
    if document_type not in VALID_DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid document type. Must be one of: {VALID_DOCUMENT_TYPES}")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    if live_photo and (not live_photo.content_type or not live_photo.content_type.startswith("image/")):
        raise HTTPException(status_code=400, detail="Live photo must be an image")
    
    # Save file
    file_path, original_name = save_upload_file(file)
    live_photo_path = None
    if live_photo:
        live_photo_path, _ = save_upload_file(live_photo)
    
    # Create record
    from app.database import DocumentRecord
    record = DocumentRecord(
        document_type=document_type,
        filename=original_name,
        status="processing",
        extracted_data={},
        validation_errors=[],
        tampering_details={}
    )
    
    # Temporarily store file path for processing
    record.extracted_data = {"file_path": file_path}
    db.add(record)
    db.commit()
    db.refresh(record)
    
    # Process synchronously (in production, use background tasks)
    try:
        result = screen_document(record.id, file_path, document_type, db, live_photo_path)
        return DocumentUploadResponse(
            document_id=record.id,
            filename=original_name,
            status=result.status,
            message="Document processed successfully"
        )
    except Exception as e:
        logger.error(f"Error processing document: {e}", exc_info=True)
        record.status = "failed"
        record.notes = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


def screen_document(
    document_id: int,
    file_path: str,
    document_type: str,
    db: Session,
    live_photo_path: Optional[str] = None,
) -> DocumentRecordResponse:
    """Complete document screening pipeline."""
    from app.database import DocumentRecord
    
    # Module 1: OCR Extraction
    ocr_data = document_ocr.process_document(file_path, document_type)
    
    # Module 2: Document Validation
    validation_result = document_validator.validate_document(ocr_data, document_type)
    
    # Module 3: Tampering Detection
    tampering_result = tampering_detector.detect_tampering(file_path)
    
    # Module 4: Compare the document portrait to an optional live capture.
    if live_photo_path:
        face_result = face_verifier.verify_faces(file_path, live_photo_path)
    else:
        from app.models.schemas import FaceMatchResult
        face_result = FaceMatchResult(
            score=0.0,
            match=None,
            confidence=0.0,
        )
    
    # Risk Assessment
    risk_assessment = risk_scorer.calculate_risk(tampering_result, validation_result, face_result)
    
    # Determine final status
    if risk_assessment.risk_level == "low":
        final_status = "cleared"
    elif risk_assessment.risk_level == "medium":
        final_status = "review"
    else:
        final_status = "flagged"
    
    # Update record in database
    record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
    if record:
        extracted = {
            "name": ocr_data.name,
            "passport_number": ocr_data.passport_number,
            "nationality": ocr_data.nationality,
            "date_of_birth": ocr_data.date_of_birth,
            "date_of_expiry": ocr_data.date_of_expiry,
            "gender": ocr_data.gender,
            "visa_number": ocr_data.visa_number,
            "visa_type": ocr_data.visa_type,
            "document_number": ocr_data.document_number
        }
        if getattr(ocr_data, "mrz_valid", None) is not None:
            extracted["mrz_valid"] = ocr_data.mrz_valid
        record.extracted_data = {k: v for k, v in extracted.items() if v is not None}
        record.is_valid = validation_result.is_valid
        record.validation_errors = validation_result.errors + validation_result.warnings
        record.tampering_score = tampering_result.score
        record.tampering_details = tampering_result.details
        record.has_tampering = tampering_result.has_tampering
        record.face_match_score = face_result.score
        record.face_match = face_result.match
        record.risk_score = risk_assessment.risk_score
        record.risk_level = risk_assessment.risk_level
        record.status = final_status
        db.commit()
        db.refresh(record)
    
    # Return screening result
    return DocumentRecordResponse(
        id=document_id,
        document_type=document_type,
        filename=record.filename if record else "",
        upload_time=record.upload_time if record else datetime.utcnow(),
        extracted_data=record.extracted_data if record else None,
        is_valid=record.is_valid if record else False,
        validation_errors=record.validation_errors if record else None,
        tampering_score=record.tampering_score if record else 0,
        has_tampering=record.has_tampering if record else False,
        face_match_score=record.face_match_score if record else 0,
        face_match=record.face_match if record else False,
        risk_score=record.risk_score if record else 0,
        risk_level=record.risk_level if record else "unknown",
        status=record.status if record else "failed",
        notes=record.notes if record else None
    )


@router.get("/screening/results")
async def get_all_results(db: Session = Depends(get_db)):
    """Get all screening results."""
    from app.database import DocumentRecord
    records = db.query(DocumentRecord).order_by(DocumentRecord.upload_time.desc()).all()
    return records


@router.get("/screening/{document_id}", response_model=DocumentRecordResponse)
async def get_screening_result(document_id: int, db: Session = Depends(get_db)):
    """Get a specific screening result."""
    from app.database import DocumentRecord
    record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentRecordResponse(
        id=record.id,
        document_type=record.document_type,
        filename=record.filename,
        upload_time=record.upload_time,
        extracted_data=record.extracted_data,
        is_valid=record.is_valid,
        validation_errors=record.validation_errors,
        tampering_score=record.tampering_score,
        has_tampering=record.has_tampering,
        face_match_score=record.face_match_score,
        face_match=record.face_match,
        risk_score=record.risk_score,
        risk_level=record.risk_level,
        status=record.status,
        notes=record.notes
    )


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    from app.database import DocumentRecord
    
    records = db.query(DocumentRecord).all()
    
    total = len(records)
    flagged = sum(1 for r in records if r.status == "flagged")
    high_risk = sum(1 for r in records if r.risk_level in ["high", "critical"])
    
    # Documents by type
    by_type = {}
    for r in records:
        by_type[r.document_type] = by_type.get(r.document_type, 0) + 1
    
    # Risk distribution
    risk_dist = {}
    for r in records:
        risk_dist[r.risk_level or "unknown"] = risk_dist.get(r.risk_level or "unknown", 0) + 1
    
    return DashboardStats(
        total_documents=total,
        flagged_documents=flagged,
        high_risk_count=high_risk,
        average_processing_time=15.0,  # Placeholder
        documents_by_type=by_type,
        risk_distribution=risk_dist
    )


@router.post("/screening/{document_id}/decision")
async def make_decision(document_id: int, decision: str, notes: str = "", db: Session = Depends(get_db)):
    """Take action on a flagged document."""
    from app.database import DocumentRecord
    
    if decision not in ["approve", "reject", "manual_review"]:
        raise HTTPException(status_code=400, detail="Invalid decision")
    
    record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    
    record.status = "approved" if decision == "approve" else "rejected" if decision == "reject" else "manual_review"
    if notes:
        record.notes = notes
    
    db.commit()
    
    return {"message": f"Decision '{decision}' recorded for document {document_id}", "status": record.status}
