from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
import xml.etree.ElementTree as ET

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]

class ValidationRule(ABC):
    @abstractmethod
    def validate(self, record: ET.Element) -> Optional[str]:
        """Returns an error message if validation fails, None otherwise."""
        pass

class ValidatorInterface(ABC):
    @abstractmethod
    def validate(self, record: str) -> ValidationResult:
        pass

class GeoNetworkValidator(ValidatorInterface):
    def __init__(self, rules: List[ValidationRule]):
        self.rules = rules

    def validate(self, record_xml: str) -> ValidationResult:
        errors = []
        try:
            # Parse XML
            root = ET.fromstring(record_xml)
            
            # Run all rules
            for rule in self.rules:
                error = rule.validate(root)
                if error:
                    errors.append(error)
                    
        except ET.ParseError as e:
            errors.append(f"XML Parse Error: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors)
            
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
