"""MRZ (Machine Readable Zone) parser with ICAO 9303 checksum validation.

Implements parsing of TD1, TD2, and TD3 (passport) MRZ formats from
identity documents, including checksum verification per ICAO 9303.
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ICAO 9303 character-to-value mapping
CHAR_VALUES = {
    '<': 0,
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4,
    '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14, 'F': 15,
    'G': 16, 'H': 17, 'I': 18, 'J': 19, 'K': 20, 'L': 21,
    'M': 22, 'N': 23, 'O': 24, 'P': 25, 'Q': 26, 'R': 27,
    'S': 28, 'T': 29, 'U': 30, 'V': 31, 'W': 32, 'X': 33,
    'Y': 34, 'Z': 35,
}

WEIGHTS = [7, 3, 1]


@dataclass
class MRZResult:
    """Structure for parsed MRZ data and validation results."""
    format_type: str  # TD1, TD2, TD3
    document_type: str = ""
    country_code: str = ""
    document_number: Optional[str] = None
    document_number_check: Optional[str] = None
    date_of_birth: Optional[str] = None
    date_of_birth_check: Optional[str] = None
    expiry_date: Optional[str] = None
    expiry_date_check: Optional[str] = None
    nationality: Optional[str] = None
    sex: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    optional1: Optional[str] = None
    optional2: Optional[str] = None
    composite_check: Optional[str] = None
    raw_lines: List[str] = field(default_factory=list)
    checksums: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    is_valid: bool = False


def compute_checksum(input_str: str) -> int:
    """Compute ICAO 9303 checksum for a given string.

    Each character is converted to its value, then multiplied by
    repeating weights [7, 3, 1], and the sum is mod 10.
    """
    total = 0
    for i, char in enumerate(str(input_str)):
        if char in CHAR_VALUES:
            value = CHAR_VALUES[char]
        elif char.isdigit() and 0 <= int(char) <= 9:
            value = int(char)
        elif char.isalpha():
            value = ord(char.upper()) - ord('A') + 10
        else:
            value = 0
        total += value * WEIGHTS[i % 3]
    return total % 10


def parse_date(date_str: str) -> Optional[str]:
    """Parse MRZ date (YYMMDD) into DD/MM/YYYY format."""
    if not date_str or len(date_str) != 6:
        return None
    try:
        yy = int(date_str[0:2])
        mm = int(date_str[2:4])
        dd = int(date_str[4:6])
        year = 2000 + yy if yy < 70 else 1900 + yy
        return f"{dd:02d}/{mm:02d}/{year}"
    except (ValueError, IndexError):
        return None


class MRZParser:
    """Parse MRZ from document OCR text and validate checksums."""

    def from_text(self, text: str) -> MRZResult:
        """Parse MRZ lines from raw OCR text."""
        # Extract lines that look like MRZ lines (long, uppercase, contains < or digits)
        lines = []
        for raw_line in text.split('\n'):
            line = raw_line.strip().upper()
            # MRZ lines are typically 30-44 chars (tolerate up to 50 for OCR noise)
            if 25 <= len(line) <= 50 and (line.count('<') > 3 or (len(line) > 30 and line[-1].isdigit())):
                # Remove spaces that may have been introduced by OCR
                line = line.replace(' ', '')
                lines.append(line)

        if not lines:
            return MRZResult(format_type="unknown", document_type="", country_code="",
                             errors=["No MRZ lines detected"])

        # Order lines by length descending to find MRZ lines
        lines = sorted(set(lines), key=len, reverse=True)

        # Try TD3 (passport): 2 lines of 44 chars
        if len(lines) >= 2 and len(lines[0]) >= 40 and len(lines[1]) >= 35:
            return self._parse_td3(lines[0][:44], lines[1][:44])

        # Try TD1: 3 lines of 30 chars
        if len(lines) >= 3 and all(25 <= len(l) <= 30 for l in lines[:3]):
            return self._parse_td1(
                lines[0][:30], lines[1][:30], lines[2][:30]
            )

        # Try TD2: 2 lines of 36 chars
        if len(lines) >= 2 and 30 <= len(lines[0]) <= 36 and 30 <= len(lines[1]) <= 40:
            return self._parse_td2(lines[0][:36], lines[1][:36])

        return MRZResult(
            format_type="unknown",
            document_type="",
            country_code="",
            raw_lines=lines,
            errors=["Could not determine MRZ format"]
        )

    def _parse_td3(self, line1: str, line2: str) -> MRZResult:
        """Parse TD3 (passport) - 2 lines of 44 characters."""
        line1 = line1.ljust(44, '<')
        line2 = line2.ljust(44, '<')
        result = MRZResult(format_type="TD3", raw_lines=[line1, line2])

        # Line 1: P<USASURNAME<<GIVEN
        result.document_type = line1[0]
        result.country_code = line1[2:5]
        # Name split at << between last and first name
        name_field = line1[5:44].rstrip('<')
        if '<<' in name_field:
            parts = name_field.split('<<', 1)
            result.last_name = parts[0].replace('<', ' ')
            result.first_name = parts[1].replace('<', ' ')
        else:
            result.last_name = name_field.replace('<', ' ')

        # Line 2: DOCNUMBER<CHECK1COUNTRYDOB<CHECK2SEXEXPIRY<CHECK3PERSONAL<CHECK4
        result.document_number = line2[0:9]
        result.document_number_check = line2[9]
        result.nationality = line2[10:13]
        result.date_of_birth = parse_date(line2[13:19])
        result.date_of_birth_check = line2[19]
        result.sex = line2[20]
        result.expiry_date = parse_date(line2[21:27])
        result.expiry_date_check = line2[27]
        result.optional1 = line2[28:43].replace('<', ' ')
        result.composite_check = line2[43]

        return self._validate(result)

    def _parse_td1(self, line1: str, line2: str, line3: str) -> MRZResult:
        """Parse TD1 (ID card) - 3 lines of 30 characters."""
        line1 = line1.ljust(30, '<')
        line2 = line2.ljust(30, '<')
        line3 = line3.ljust(30, '<')
        result = MRZResult(format_type="TD1", raw_lines=[line1, line2, line3])

        result.document_type = line1[0]
        result.country_code = line1[2:5]
        result.document_number = line1[5:14]
        result.document_number_check = line1[14]
        result.optional1 = line1[15:30].replace('<', ' ')

        result.date_of_birth = parse_date(line2[0:6])
        result.date_of_birth_check = line2[6]
        result.sex = line2[7]
        result.expiry_date = parse_date(line2[8:14])
        result.expiry_date_check = line2[14]
        result.nationality = line2[15:18]
        result.optional2 = line2[18:30].replace('<', ' ')
        result.composite_check = line2[29]

        # Line 3: surname<<given names
        name_field = line3.rstrip('<')
        if '<<' in name_field:
            parts = name_field.split('<<', 1)
            result.last_name = parts[0].replace('<', ' ')
            result.first_name = parts[1].replace('<', ' ')
        else:
            result.last_name = name_field.replace('<', ' ')

        return self._validate(result)

    def _parse_td2(self, line1: str, line2: str) -> MRZResult:
        """Parse TD2 - 2 lines of 36 characters."""
        line1 = line1.ljust(36, '<')
        line2 = line2.ljust(36, '<')
        result = MRZResult(format_type="TD2", raw_lines=[line1, line2])

        result.document_type = line1[0]
        result.country_code = line1[2:5]
        name_field = line1[5:36].rstrip('<')
        if '<<' in name_field:
            parts = name_field.split('<<', 1)
            result.last_name = parts[0].replace('<', ' ')
            result.first_name = parts[1].replace('<', ' ')
        else:
            result.last_name = name_field.replace('<', ' ')

        result.document_number = line2[0:9]
        result.document_number_check = line2[9]
        result.nationality = line2[10:13]
        result.date_of_birth = parse_date(line2[13:19])
        result.date_of_birth_check = line2[19]
        result.sex = line2[20]
        result.expiry_date = parse_date(line2[21:27])
        result.expiry_date_check = line2[27]
        result.optional1 = line2[28:35].replace('<', ' ')
        result.composite_check = line2[35]

        return self._validate(result)

    def _validate(self, result: MRZResult) -> MRZResult:
        """Validate all checksums and set is_valid flag."""
        checks = {
            'document_number': (result.document_number, result.document_number_check),
            'date_of_birth': (result.date_of_birth, result.date_of_birth_check),
            'expiry_date': (result.expiry_date, result.expiry_date_check),
            'composite': (None, result.composite_check),
        }

        for field, (value, check_char) in checks.items():
            if value is not None and check_char:
                # Compute checksum over the numeric/string value
                if field == 'date_of_birth' and value:
                    # Reconstruct YYMMDD from parsed date
                    try:
                        dd, mm, yyyy = value.split('/')
                        yy = str(int(yyyy))[-2:]
                        checksum_input = f"{yy}{mm}{dd}"
                    except ValueError:
                        continue
                elif field == 'expiry_date' and value:
                    try:
                        dd, mm, yyyy = value.split('/')
                        yy = str(int(yyyy))[-2:]
                        checksum_input = f"{yy}{mm}{dd}"
                    except ValueError:
                        continue
                else:
                    checksum_input = value

                computed = compute_checksum(checksum_input)
                expected = int(check_char) if check_char.isdigit() else None

                if expected is not None:
                    valid = computed == expected
                    result.checksums[field] = "valid" if valid else "invalid"
                    if not valid:
                        result.errors.append(
                            f"{field} checksum mismatch (expected {check_char}, got {computed})"
                        )

        result.is_valid = len(result.errors) == 0
        return result


mrz_parser = MRZParser()
