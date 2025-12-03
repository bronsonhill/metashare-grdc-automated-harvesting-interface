from typing import Optional, List
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod

NAMESPACES = {
    "mdb": "http://standards.iso.org/iso/19115/-3/mdb/2.0",
    "cit": "http://standards.iso.org/iso/19115/-3/cit/2.0",
    "gco": "http://standards.iso.org/iso/19115/-3/gco/1.0",
    "mri": "http://standards.iso.org/iso/19115/-3/mri/1.0",
    "mcc": "http://standards.iso.org/iso/19115/-3/mcc/1.0",
    "gex": "http://standards.iso.org/iso/19115/-3/gex/1.0",
    "gml": "http://www.opengis.net/gml/3.2",
    "mrs": "http://standards.iso.org/iso/19115/-3/mrs/1.0",
}

class ValidationRule(ABC):
    @abstractmethod
    def validate(self, record: ET.Element) -> Optional[str]:
        """Returns an error message if validation fails, None otherwise."""
        pass

class FieldExistsRule(ValidationRule):
    def __init__(self, xpath: str, field_name: str):
        self.xpath = xpath
        self.field_name = field_name

    def validate(self, record: ET.Element) -> Optional[str]:
        if "/@" in self.xpath:
            element_path, attr_name = self.xpath.split("/@")
            node = record.find(element_path, NAMESPACES)
            if node is None:
                return f"Record is missing a {self.field_name} (element not found)."
            value = node.get(attr_name)
            if not value or not value.strip():
                return f"Record is missing a {self.field_name} (attribute {attr_name} missing or empty)."
        else:
            node = record.find(self.xpath, NAMESPACES)
            if node is None or not node.text or not node.text.strip():
                return f"Record is missing a {self.field_name}."
        return None

class ValueInListRule(ValidationRule):
    def __init__(self, xpath: str, allowed_values: List[str], field_name: str):
        self.xpath = xpath
        self.allowed_values = allowed_values
        self.field_name = field_name

    def validate(self, record: ET.Element) -> Optional[str]:
        value = None
        if "/@" in self.xpath:
            element_path, attr_name = self.xpath.split("/@")
            node = record.find(element_path, NAMESPACES)
            if node is not None:
                value = node.get(attr_name)
        else:
            node = record.find(self.xpath, NAMESPACES)
            if node is not None:
                value = node.text
            
        if value:
            value = value.strip()
        
        # If value is missing, is it valid? Assuming this rule only checks validity IF it exists.
        # But if it's mandatory, FieldExistsRule should be used too.
        # If node is missing, value is None.
        
        if value and value not in self.allowed_values:
            return f"Record has an invalid {self.field_name}: {value}"
        return None

class FloatRule(ValidationRule):
    def __init__(self, xpath: str, field_name: str):
        self.xpath = xpath
        self.field_name = field_name
    
    def validate(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        try:
            float(node.text.strip())
            return None
        except ValueError:
            return f"Record has an invalid float: {node.text.strip()}"


class DateRule(ValidationRule):
    def __init__(self, xpath: str, field_name: str):
        self.xpath = xpath
        self.field_name = field_name
    
    def validate(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        try:
            datetime.datetime.strptime(node.text.strip(), "%d-%m-%Y")
            return None
        except ValueError:
            return f"Record has an invalid date: {node.text.strip()}"

class ValidPurposeRule(ValidationRule):
    def __init__(self, xpath: str, field_name: str):
        self.xpath = xpath
        self.field_name = field_name
    
    def validate(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        try:
            datetime.datetime.strptime(node.text.strip(), "%d-%m-%Y")
            return None
        except ValueError:
            return f"Record has an invalid date: {node.text.strip()}"


class IdentifierRule(ValidationRule):
    def __init__(self, xpath: str, field_name: str):
        self.xpath = xpath
        self.field_name = field_name
    
    def validate(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        try:
            # check for doi, handle or url
            if self._valid_doi(record):
                return self._valid_doi(record)
            if self._valid_handle(record):
                return self._valid_handle(record)
            if self._valid_url(record):
                return self._valid_url(record)
        except ValueError:
            return f"Record has an invalid identifier: {node.text.strip()}"
    
    def _valid_doi(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        if node is None or not node.text:
            return None
        try:
            # check for doi prefix
            if not node.text.startswith("10."):
                return f"Record has an invalid doi: {node.text.strip()}"
            return None
        except ValueError:
            return f"Record has an invalid doi: {node.text.strip()}"

    def _valid_handle(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        if node is None or not node.text:
            return None
        try:
            # check for handle prefix
            if not node.text.startswith("http://hdl.handle.net/"):
                return f"Record has an invalid handle: {node.text.strip()}"
            return None
        except ValueError:
            return f"Record has an invalid handle: {node.text.strip()}"

    def _valid_url(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        if node is None or not node.text:
            return None
        try:
            # check for url prefix
            if not node.text.startswith("http://") and not node.text.startswith("https://"):
                return f"Record has an invalid url: {node.text.strip()}"
            return None
        except ValueError:
            return f"Record has an invalid url: {node.text.strip()}"


class CitationRule(ValidationRule):
    def __init__(self, xpath: str, field_name: str):
        self.xpath = xpath
        self.field_name = field_name
    
    def validate(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        if node is None or not node.text:
            return None
        try:
            # check for citation prefix
            if not node.text.startswith("http://") and not node.text.startswith("https://"):
                return f"Record has an invalid citation: {node.text.strip()}"
            return None
        except ValueError:
            return f"Record has an invalid citation: {node.text.strip()}"

    def _valid_given_name(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        if node is None or not node.text:
            return None
        try:
            # check for given name
            if not node.text.strip():
                return f"Record has an invalid given name: {node.text.strip()}"
            return None
        except ValueError:
            return f"Record has an invalid given name: {node.text.strip()}"
    
    def _valid_family_name(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        if node is None or not node.text:
            return None
        try:
            # check for family name
            if not node.text.strip():
                return f"Record has an invalid family name: {node.text.strip()}"
            return None
        except ValueError:
            return f"Record has an invalid family name: {node.text.strip()}"
    
    def _valid_orcid(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        if node is None or not node.text:
            return None
        try:
            # check for orcid prefix
            if not node.text.startswith("http://orcid.org/"):
                return f"Record has an invalid orcid: {node.text.strip()}"
            return None
        except ValueError:
            return f"Record has an invalid orcid: {node.text.strip()}"
    
    def _valid_role(self, record: ET.Element) -> Optional[str]:
        node = record.find(self.xpath, NAMESPACES)
        if node is None or not node.text:
            return None
        try:
            # check for role
            if not node.text.strip():
                return f"Record has an invalid role: {node.text.strip()}"
            return None
        except ValueError:
            return f"Record has an invalid role: {node.text.strip()}"