from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import get_settings

settings = get_settings()


def _make_engine():
    url = settings.DATABASE_URL
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(url, connect_args=connect_args)


engine = _make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DocumentRecord(Base):
    __tablename__ = "document_records"
    
    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String(50))  # passport, visa, national_id, driving_license
    filename = Column(String(255))
    upload_time = Column(DateTime, default=datetime.utcnow)
    
    # OCR Extracted Data
    extracted_data = Column(JSON)
    
    # Validation Results
    is_valid = Column(Boolean, default=False)
    validation_errors = Column(JSON)
    
    # Tampering Detection
    tampering_score = Column(Float, default=0.0)
    tampering_details = Column(JSON)
    has_tampering = Column(Boolean, default=False)
    
    # Face Verification
    face_match_score = Column(Float, default=0.0)
    face_match = Column(Boolean, default=False)
    
    # Overall Risk Assessment
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20))  # low, medium, high, critical
    
    # Status
    status = Column(String(20), default="pending")  # pending, processed, flagged
    notes = Column(Text)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    action = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)
    operator = Column(String(100))


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
