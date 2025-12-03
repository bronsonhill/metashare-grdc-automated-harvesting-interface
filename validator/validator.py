from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from .rules import *
from config import ConfigLoader

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]

class ValidatorInterface(ABC):
    @abstractmethod
    def validate(self, record: str) -> ValidationResult:
        pass

class GeoNetworkValidator(ValidatorInterface):
    def __init__(self):
        self.validator_config = ConfigLoader().validator_config
        self.rules = []
        self._set_rules()

    def validate(self, record_xml: str) -> ValidationResult:
        errors = []
        try:
            # Parse XML
            root = ET.fromstring(record_xml)

            print(f"Validating record: {root.find('mdb:identificationInfo/mri:MD_DataIdentification/mri:citation/cit:CI_Citation/cit:title/gco:CharacterString', NAMESPACES).text}")
            
            # Run all rules
            for rule in self.rules:
                error = rule.validate(root)
                if error:
                    errors.append(error)
                    
        except ET.ParseError as e:
            errors.append(f"XML Parse Error: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors)
            
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def _set_rules(self):
        for rule in self.validator_config.rules:
            if rule.type == "field_exists":
                self.rules.append(FieldExistsRule(rule.xpath, rule.field_name))
            elif rule.type == "value_in_list":
                self.rules.append(ValueInListRule(rule.xpath, rule.allowed_values, rule.field_name))
            elif rule.type == "float":
                self.rules.append(FloatRule(rule.xpath, rule.field_name))
            elif rule.type == "date":
                self.rules.append(DateRule(rule.xpath, rule.field_name))
            elif rule.type == "valid_purpose":
                self.rules.append(ValidPurposeRule(rule.xpath, rule.field_name))
            elif rule.type == "identifier":
                self.rules.append(IdentifierRule(rule.xpath, rule.field_name))
            elif rule.type == "citation":
                self.rules.append(CitationRule(rule.xpath, rule.field_name))

