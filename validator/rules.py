from typing import Optional, List
import xml.etree.ElementTree as ET
from .validator import ValidationRule

NAMESPACES = {
    "mdb": "http://standards.iso.org/iso/19115/-3/mdb/2.0",
    "cit": "http://standards.iso.org/iso/19115/-3/cit/2.0",
    "gco": "http://standards.iso.org/iso/19115/-3/gco/1.0",
    "mri": "http://standards.iso.org/iso/19115/-3/mri/1.0",
}

class CheckFieldExists(ValidationRule):
    def __init__(self, xpath: str, field_name: str):
        self.xpath = xpath
        self.field_name = field_name

    def validate(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        if node is None or not node.text or not node.text.strip():
            return f"Record is missing a {self.field_name}."
        return None

class CheckValueInList(ValidationRule):
    def __init__(self, xpath: str, allowed_values: List[str], field_name: str):
        self.xpath = xpath
        self.allowed_values = allowed_values
        self.field_name = field_name

    def validate(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        # If missing, we assume CheckFieldExists caught it, or it's optional
        if node is None or not node.text:
            return None
            
        value = node.text.strip()
        if value not in self.allowed_values:
            return f"Record has an invalid {self.field_name}: {value}"
        return None