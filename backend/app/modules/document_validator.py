import re
from datetime import datetime, date
from typing import List, Tuple
from app.models.schemas import OCRData, ValidationResult


class DocumentValidator:
    """Module 2: Validate extracted document data against official standards."""
    
    # Valid country codes (ISO 3166-1 alpha-2)
    VALID_COUNTRY_CODES = {
        "AF", "AL", "DZ", "AD", "AO", "AG", "AR", "AM", "AU", "AT", "AZ",
        "BS", "BH", "BD", "BB", "BY", "BE", "BZ", "BJ", "BT", "BO", "BA",
        "BW", "BR", "BN", "BG", "BF", "BI", "CV", "KH", "CM", "CA", "CF",
        "TD", "CL", "CN", "CO", "KM", "CG", "CD", "CR", "CI", "HR", "CU",
        "CY", "CZ", "DK", "DJ", "DM", "DO", "EC", "EG", "SV", "GQ", "ER",
        "EE", "SZ", "ET", "FJ", "FI", "FR", "GA", "GM", "GE", "DE", "GH",
        "GR", "GD", "GT", "GN", "GW", "GY", "HT", "HN", "HU", "IS", "IN",
        "ID", "IR", "IQ", "IE", "IL", "IT", "JM", "JP", "JO", "KZ", "KE",
        "KI", "KP", "KR", "KW", "KG", "LA", "LV", "LB", "LS", "LR", "LY",
        "LI", "LT", "LU", "MG", "MW", "MY", "MV", "ML", "MT", "MH", "MR",
        "MU", "MX", "FM", "MD", "MC", "MN", "ME", "MA", "MZ", "MM", "NA",
        "NR", "NP", "NL", "NZ", "NI", "NE", "NG", "MK", "NO", "OM", "PK",
        "PW", "PA", "PG", "PY", "PE", "PH", "PL", "PT", "QA", "RO", "RU",
        "RW", "KN", "LC", "VC", "WS", "SM", "ST", "SA", "SN", "RS", "SC",
        "SL", "SG", "SK", "SI", "SB", "SO", "ZA", "SS", "ES", "LK", "SD",
        "SR", "SE", "CH", "SY", "TW", "TJ", "TZ", "TH", "TL", "TG", "TO",
        "TT", "TN", "TR", "TM", "TV", "UG", "UA", "AE", "GB", "US", "UY",
        "UZ", "VU", "VE", "VN", "YE", "ZM", "ZW"
    }
    
    # Passport format patterns by country
    PASSPORT_PATTERNS = {
        "US": r"^[A-Z]\d{8}$",
        "UK": r"^\d{9}$",
        "IN": r"^[A-Z]\d{7}$",
        "DE": r"^[CFGHJKLMNPRTVWXYZ\d]{9}$",
        "FR": r"^\d{9}$",
        "JP": r"^[A-Z]{2}\d{7}$",
        "DEFAULT": r"^[A-Z0-9]{5,15}$"
    }
    
    def validate_date(self, date_str: str) -> Tuple[bool, str]:
        """Validate date format and check if it's reasonable."""
        if not date_str:
            return False, "Date not provided"
        
        # Try different formats
        formats = ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y"]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                
                # Check if date is in reasonable range
                today = date.today()
                
                # Not too far in the past (100 years)
                if (today - parsed).days > 36500:
                    return False, f"Date too far in the past: {date_str}"
                
                # Not too far in the future (20 years)
                if (parsed - today).days > 7300:
                    return False, f"Date too far in the future: {date_str}"
                
                return True, "Valid date"
            except ValueError:
                continue
        
        return False, f"Invalid date format: {date_str}"
    
    def validate_passport_number(self, number: str, country_code: str = None) -> Tuple[bool, str]:
        """Validate passport number format."""
        if not number:
            return False, "Passport number not provided"
        
        # Clean the number
        number = number.strip().upper()
        
        # Get pattern for country or default
        pattern = self.PASSPORT_PATTERNS.get(country_code, self.PASSPORT_PATTERNS["DEFAULT"])
        
        if re.match(pattern, number):
            return True, "Valid passport number format"
        
        return False, f"Invalid passport number format: {number}"
    
    def validate_expiry(self, expiry_date: str) -> Tuple[bool, str]:
        """Check if document has expired."""
        if not expiry_date:
            return False, "Expiry date not provided"
        
        is_valid, msg = self.validate_date(expiry_date)
        if not is_valid:
            return False, msg
        
        # Parse and check expiry
        formats = ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"]
        for fmt in formats:
            try:
                expiry = datetime.strptime(expiry_date, fmt).date()
                today = date.today()
                
                if expiry < today:
                    return False, f"Document has expired on {expiry_date}"
                
                # Warning if expiring within 3 months
                days_until_expiry = (expiry - today).days
                if days_until_expiry < 90:
                    return True, f"Warning: Document expires in {days_until_expiry} days"
                
                return True, "Document is valid"
            except ValueError:
                continue
        
        return False, "Could not validate expiry date"
    
    def validate_name(self, name: str) -> Tuple[bool, str]:
        """Validate name field."""
        if not name:
            return False, "Name not provided"
        
        name = name.strip()
        
        # Check minimum length
        if len(name) < 2:
            return False, "Name too short"
        
        # Check for suspicious characters
        if re.search(r'[0-9]', name):
            return False, "Name contains numbers"
        
        if re.search(r"[!@#$%^&*()_+=\[\]{};:'\"\\|,.<>/?]", name):
            return False, "Name contains special characters"
        
        return True, "Valid name"
    
    def validate_mrz_checksums(self, ocr_data: OCRData) -> List[str]:
        """Validate MRZ checksums (ICAO 9303). Returns list of errors."""
        errors = []
        if getattr(ocr_data, "mrz_valid", None) is not None and not ocr_data.mrz_valid:
            errors.append("MRZ checksum validation failed (document number, DOB, or expiry mismatch)")
        return errors

    def validate_document(self, ocr_data: OCRData, document_type: str) -> ValidationResult:
        """Main validation pipeline."""
        errors = []
        warnings = []
        
        # MRZ checksum validation (applies to MRZ-capable documents)
        errors.extend(self.validate_mrz_checksums(ocr_data))
        
        # Validate based on document type
        if document_type == "passport":
            # Name validation
            is_valid, msg = self.validate_name(ocr_data.name or "")
            if not is_valid:
                errors.append(f"Name: {msg}")
            
            # Passport number
            is_valid, msg = self.validate_passport_number(ocr_data.passport_number or "")
            if not is_valid:
                errors.append(f"Passport Number: {msg}")
            
            # Date of birth
            is_valid, msg = self.validate_date(ocr_data.date_of_birth or "")
            if not is_valid:
                errors.append(f"Date of Birth: {msg}")
            
            # Expiry validation
            is_valid, msg = self.validate_expiry(ocr_data.date_of_expiry or "")
            if not is_valid:
                errors.append(f"Expiry: {msg}")
            elif "Warning" in msg:
                warnings.append(msg)
            
            # Gender validation
            if ocr_data.gender and ocr_data.gender.upper() not in ["M", "F", "MALE", "FEMALE"]:
                errors.append(f"Invalid gender value: {ocr_data.gender}")
        
        elif document_type == "visa":
            if not ocr_data.visa_number:
                errors.append("Visa number not found")
            if not ocr_data.visa_type:
                warnings.append("Visa type not detected")
        
        elif document_type == "national_id":
            if not ocr_data.document_number:
                errors.append("ID number not found")
            is_valid, msg = self.validate_date(ocr_data.date_of_birth or "")
            if not is_valid:
                errors.append(f"Date of Birth: {msg}")
        
        elif document_type == "driving_license":
            if not ocr_data.document_number:
                errors.append("License number not found")
        
        # General checks
        if not ocr_data.raw_text or len(ocr_data.raw_text) < 50:
            warnings.append("Low text content detected - document may be blurry or damaged")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


document_validator = DocumentValidator()
