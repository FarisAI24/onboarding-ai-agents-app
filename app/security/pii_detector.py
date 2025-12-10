"""PII Detection and Redaction module."""
import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PIIType(str, Enum):
    """Types of PII that can be detected."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    ADDRESS = "address"
    NAME = "name"


@dataclass
class PIIMatch:
    """A detected PII match."""
    pii_type: PIIType
    original: str
    start: int
    end: int
    redacted: str = "[REDACTED]"
    confidence: float = 1.0


@dataclass
class PIIDetectionResult:
    """Result of PII detection."""
    original_text: str
    redacted_text: str
    matches: List[PIIMatch] = field(default_factory=list)
    pii_found: bool = False
    pii_types_found: List[PIIType] = field(default_factory=list)


class PIIDetector:
    """Detects and redacts PII from text."""
    
    # Regex patterns for various PII types
    PATTERNS = {
        PIIType.EMAIL: (
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "[EMAIL_REDACTED]"
        ),
        PIIType.PHONE: (
            r'\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b',
            "[PHONE_REDACTED]"
        ),
        PIIType.SSN: (
            r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
            "[SSN_REDACTED]"
        ),
        PIIType.CREDIT_CARD: (
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            "[CC_REDACTED]"
        ),
        PIIType.IP_ADDRESS: (
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "[IP_REDACTED]"
        ),
        PIIType.DATE_OF_BIRTH: (
            r'\b(?:0?[1-9]|1[0-2])[/\-](?:0?[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b',
            "[DOB_REDACTED]"
        ),
        PIIType.PASSPORT: (
            r'\b[A-Z]{1,2}\d{6,9}\b',
            "[PASSPORT_REDACTED]"
        ),
    }
    
    # Common name prefixes and patterns
    NAME_PATTERNS = [
        (r'\bMr\.?\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b', "[NAME_REDACTED]"),
        (r'\bMrs\.?\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b', "[NAME_REDACTED]"),
        (r'\bMs\.?\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b', "[NAME_REDACTED]"),
        (r'\bDr\.?\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b', "[NAME_REDACTED]"),
    ]
    
    # Address patterns
    ADDRESS_PATTERNS = [
        (r'\b\d{1,5}\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b\.?',
         "[ADDRESS_REDACTED]"),
        (r'\b[A-Z][a-z]+,?\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?\b',
         "[ADDRESS_REDACTED]"),
    ]
    
    def __init__(
        self,
        enabled_types: List[PIIType] = None,
        custom_patterns: Dict[str, Tuple[str, str]] = None
    ):
        """Initialize the PII detector.
        
        Args:
            enabled_types: List of PII types to detect. Defaults to all.
            custom_patterns: Custom regex patterns to add.
        """
        if enabled_types is None:
            enabled_types = list(PIIType)
        
        self.enabled_types = enabled_types
        self._compiled_patterns: Dict[PIIType, Tuple[re.Pattern, str]] = {}
        
        # Compile patterns
        for pii_type, (pattern, replacement) in self.PATTERNS.items():
            if pii_type in enabled_types:
                self._compiled_patterns[pii_type] = (
                    re.compile(pattern, re.IGNORECASE),
                    replacement
                )
        
        # Add custom patterns
        if custom_patterns:
            for name, (pattern, replacement) in custom_patterns.items():
                self._compiled_patterns[name] = (
                    re.compile(pattern, re.IGNORECASE),
                    replacement
                )
        
        # Compile name and address patterns
        self._name_patterns = [
            (re.compile(p), r) for p, r in self.NAME_PATTERNS
        ]
        self._address_patterns = [
            (re.compile(p, re.IGNORECASE), r) for p, r in self.ADDRESS_PATTERNS
        ]
    
    def detect(self, text: str) -> PIIDetectionResult:
        """Detect PII in text.
        
        Args:
            text: Text to scan for PII.
            
        Returns:
            PIIDetectionResult with matches and redacted text.
        """
        if not text:
            return PIIDetectionResult(
                original_text="",
                redacted_text="",
                pii_found=False
            )
        
        matches: List[PIIMatch] = []
        
        # Check each pattern
        for pii_type, (pattern, replacement) in self._compiled_patterns.items():
            for match in pattern.finditer(text):
                matches.append(PIIMatch(
                    pii_type=pii_type,
                    original=match.group(),
                    start=match.start(),
                    end=match.end(),
                    redacted=replacement
                ))
        
        # Check name patterns if enabled
        if PIIType.NAME in self.enabled_types:
            for pattern, replacement in self._name_patterns:
                for match in pattern.finditer(text):
                    matches.append(PIIMatch(
                        pii_type=PIIType.NAME,
                        original=match.group(),
                        start=match.start(),
                        end=match.end(),
                        redacted=replacement,
                        confidence=0.8  # Lower confidence for name detection
                    ))
        
        # Check address patterns if enabled
        if PIIType.ADDRESS in self.enabled_types:
            for pattern, replacement in self._address_patterns:
                for match in pattern.finditer(text):
                    matches.append(PIIMatch(
                        pii_type=PIIType.ADDRESS,
                        original=match.group(),
                        start=match.start(),
                        end=match.end(),
                        redacted=replacement,
                        confidence=0.7
                    ))
        
        # Sort matches by start position (descending) for redaction
        matches.sort(key=lambda m: m.start, reverse=True)
        
        # Apply redactions
        redacted_text = text
        for match in matches:
            redacted_text = (
                redacted_text[:match.start] +
                match.redacted +
                redacted_text[match.end:]
            )
        
        # Get unique PII types found
        pii_types_found = list(set(m.pii_type for m in matches))
        
        return PIIDetectionResult(
            original_text=text,
            redacted_text=redacted_text,
            matches=matches,
            pii_found=len(matches) > 0,
            pii_types_found=pii_types_found
        )
    
    def redact(self, text: str) -> str:
        """Redact PII from text.
        
        Args:
            text: Text to redact.
            
        Returns:
            Redacted text.
        """
        result = self.detect(text)
        return result.redacted_text
    
    def contains_pii(self, text: str) -> bool:
        """Check if text contains PII.
        
        Args:
            text: Text to check.
            
        Returns:
            True if PII is found.
        """
        result = self.detect(text)
        return result.pii_found


# Global PII detector instance
_pii_detector: Optional[PIIDetector] = None


def get_pii_detector() -> PIIDetector:
    """Get the global PII detector instance."""
    global _pii_detector
    if _pii_detector is None:
        _pii_detector = PIIDetector()
    return _pii_detector


def redact_pii(text: str) -> str:
    """Convenience function to redact PII from text.
    
    Args:
        text: Text to redact.
        
    Returns:
        Redacted text.
    """
    return get_pii_detector().redact(text)

