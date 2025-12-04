from typing import Optional, List
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
import datetime
import re
from config import ConfigLoader


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
        namespaces = ConfigLoader().namespaces
        if "/@" in self.xpath:
            element_path, attr_name = self.xpath.split("/@")
            node = record.find(element_path, namespaces)
            if node is None:
                return f"Record is missing a {self.field_name} (element not found)"
            value = node.get(attr_name)
            if not value or not value.strip():
                return f"Record is missing a {self.field_name} (attribute {attr_name} missing or empty)"
        else:
            node = record.find(self.xpath, namespaces)
            if node is None:
                # Special handling for title to ensure we don't return None if it's really missing
                if "title" in self.field_name.lower():
                     return f"Record is missing a {self.field_name}"
                return f"Record is missing a {self.field_name}"
            
            if not node.text or not node.text.strip():
                 return f"Record is missing a {self.field_name}"
                 
        return None


class ValueInListRule(ValidationRule):
    def __init__(self, xpath: str, allowed_values: List[str], field_display_name: str):
        self.xpath = xpath
        self.allowed_values = allowed_values
        self.field_display_name = field_display_name

    def validate(self, record: ET.Element) -> Optional[str]:
        namespaces = ConfigLoader().namespaces
        if "/@" in self.xpath:
            element_path, attr_name = self.xpath.split("/@")
            node = record.find(element_path, namespaces)
            if node is None:
                return f"Record is missing {self.field_display_name} (element not found)"
            value = node.get(attr_name)
            if not value:
                return f"Record is missing {self.field_display_name} (attribute {attr_name} missing or empty)"
            if value.strip() not in self.allowed_values:
                return f"Record has an invalid {self.field_display_name}: '{value.strip()}'. Allowed values are: {', '.join(self.allowed_values)}"
        else:
            node = record.find(self.xpath, namespaces)
            if node is None or not node.text:
                return f"Record is missing {self.field_display_name}."
            
            if node.text.strip() not in self.allowed_values:
                return f"Record has an invalid {self.field_display_name}: '{node.text.strip()}'. Allowed values are: {', '.join(self.allowed_values)}"
        return None


class FloatRule(ValidationRule):
    def __init__(self, xpath: str, field_name: str):
        self.xpath = xpath
        self.field_name = field_name
    
    def validate(self, record: ET.Element) -> Optional[str]:
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
        if node is None or not node.text or not node.text.strip():
             return f"Record is missing {self.field_name}"
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
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
        if node is None or not node.text or not node.text.strip():
             return f"Record has an invalid date: {node.text.strip() if node is not None and node.text else 'None'}"
        try:
            # Try YYYY-MM-DD first
            datetime.datetime.strptime(node.text.strip(), "%Y-%m-%d")
            return None
        except ValueError:
            try:
                # Try DD-MM-YYYY as fallback
                datetime.datetime.strptime(node.text.strip(), "%d-%m-%Y")
                return None
            except ValueError:
                return f"Record has an invalid date: {node.text.strip()}"


class ValidPurposeRule(ValidationRule):
    def __init__(self, xpath: str, field_display_name: str):
        self.xpath = xpath
        self.field_display_name = field_display_name
    
    def validate(self, record: ET.Element) -> Optional[str]:
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
        if node is None or not node.text or not node.text.strip():
             return f"Record is missing {self.field_display_name}"
        # •	Purpose must be ‘GRDC contract code, project title’. Contract code is in format {A-Z}*3{0-9}*4-{0-9}*3-{A-Z}*3
        try:
            purpose = node.text.split(",")
            if len(purpose) != 2:
                return f"Record has an invalid {self.field_display_name}: {node.text.strip()}. It should be in the format 'GRDC contract code, project title'"
            contract_code = purpose[0].strip()
            if not re.match(r"^[A-Z]{3}[0-9]{4}-[0-9]{3}-?[A-Z]{3}$", contract_code):
                return f"Record has an invalid contract code: {contract_code}. It should be in the format ABC1234-567-XYZ or ABC1234-567XYZ"
            return None
        except ValueError:
            return f"Record has an invalid {self.field_display_name}: {node.text.strip()}. It should be in the format 'GRDC contract code, project title'"


class IdentifierRule(ValidationRule):
    def __init__(self, xpath: str, field_name: str):
        self.xpath = xpath
        self.field_name = field_name
    
    def validate(self, record: ET.Element) -> Optional[str]:
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
        if node is None or not node.text or not node.text.strip():
             return f"Record is missing {self.field_name}"
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
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
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
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
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
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
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
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
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
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
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
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
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
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
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
        namespaces = ConfigLoader().namespaces
        node = record.find(self.xpath, namespaces)
        if node is None or not node.text:
            return None
        try:
            # check for role
            if not node.text.strip():
                return f"Record has an invalid role: {node.text.strip()}"
            return None
        except ValueError:
            return f"Record has an invalid role: {node.text.strip()}"


class PrincipalInvestigatorRule(ValidationRule):
    def __init__(self, xpath: str, field_display_name: str):
        self.xpath = xpath
        self.field_display_name = field_display_name

    def validate(self, record: ET.Element) -> Optional[str]:
        namespaces = ConfigLoader().namespaces
        parties = record.findall(self.xpath, namespaces)
        pi_found = False
        for party in parties:
            role = party.find("cit:CI_Responsibility/cit:role/cit:CI_RoleCode", namespaces)
            if role is not None and role.get('codeListValue') == 'principalInvestigator':
                pi_found = True
                
                # Validate Name
                name = party.find(".//cit:individual/cit:CI_Individual/cit:name/gco:CharacterString", namespaces)
                if name is None or not name.text or not name.text.strip():
                     return "Principal Investigator must have a name"
                
                # Validate Email
                email = party.find(".//cit:electronicMailAddress/gco:CharacterString", namespaces)
                if email is not None and email.text:
                     if "@" not in email.text:
                         return f"Principal Investigator has invalid email: {email.text}"
                
                # Validate Orcid
                online_resources = party.findall(".//cit:onlineResource/cit:CI_OnlineResource", namespaces)
                for res in online_resources:
                    res_name = res.find("cit:name/gco:CharacterString", namespaces)
                    if res_name is not None and res_name.text in ('Orcid', 'Orchid'):
                        linkage = res.find("cit:linkage/gco:CharacterString", namespaces)
                        if linkage is not None and linkage.text:
                            if "orcid.org" not in linkage.text:
                                return f"Principal Investigator has invalid ORCID URL: {linkage.text}"

        if not pi_found:
            return "Record must have at least one Principal Investigator"
        
        return None