import os
import copy
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Dict

# Define namespaces
NAMESPACES = {
    'mdb': 'http://standards.iso.org/iso/19115/-3/mdb/2.0',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'cat': 'http://standards.iso.org/iso/19115/-3/cat/1.0',
    'gfc': 'http://standards.iso.org/iso/19110/gfc/1.1',
    'cit': 'http://standards.iso.org/iso/19115/-3/cit/2.0',
    'gcx': 'http://standards.iso.org/iso/19115/-3/gcx/1.0',
    'gex': 'http://standards.iso.org/iso/19115/-3/gex/1.0',
    'lan': 'http://standards.iso.org/iso/19115/-3/lan/1.0',
    'srv': 'http://standards.iso.org/iso/19115/-3/srv/2.1',
    'mas': 'http://standards.iso.org/iso/19115/-3/mas/1.0',
    'mcc': 'http://standards.iso.org/iso/19115/-3/mcc/1.0',
    'mco': 'http://standards.iso.org/iso/19115/-3/mco/1.0',
    'mda': 'http://standards.iso.org/iso/19115/-3/mda/1.0',
    'mds': 'http://standards.iso.org/iso/19115/-3/mds/2.0',
    'mdt': 'http://standards.iso.org/iso/19115/-3/mdt/2.0',
    'mex': 'http://standards.iso.org/iso/19115/-3/mex/1.0',
    'mmi': 'http://standards.iso.org/iso/19115/-3/mmi/1.0',
    'mpc': 'http://standards.iso.org/iso/19115/-3/mpc/1.0',
    'mrc': 'http://standards.iso.org/iso/19115/-3/mrc/2.0',
    'mrd': 'http://standards.iso.org/iso/19115/-3/mrd/1.0',
    'mri': 'http://standards.iso.org/iso/19115/-3/mri/1.0',
    'mrl': 'http://standards.iso.org/iso/19115/-3/mrl/2.0',
    'mrs': 'http://standards.iso.org/iso/19115/-3/mrs/1.0',
    'msr': 'http://standards.iso.org/iso/19115/-3/msr/2.0',
    'mdq': 'http://standards.iso.org/iso/19157/-2/mdq/1.0',
    'mac': 'http://standards.iso.org/iso/19115/-3/mac/2.0',
    'gco': 'http://standards.iso.org/iso/19115/-3/gco/1.0',
    'gml': 'http://www.opengis.net/gml/3.2',
    'xlink': 'http://www.w3.org/1999/xlink'
}

# Register namespaces for parsing/writing
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_XML_PATH = os.path.join(BASE_DIR, 'valid.xml')
INVALID_OUTPUT_DIR = os.path.join(BASE_DIR, 'generated_invalid')
VALID_OUTPUT_DIR = os.path.join(BASE_DIR, 'generated_valid')

class ActionType(Enum):
    SET_TEXT = auto()
    SET_ATTRIBUTE = auto()
    REMOVE_ELEMENT = auto()
    CUSTOM_PI_EMAIL = auto()
    CUSTOM_PI_ORCID = auto()
    CUSTOM_REMOVE_PI = auto()
    CUSTOM_PI_MISSING_NAME = auto()

@dataclass
class TestCase:
    name: str
    action: ActionType
    description: str
    xpath: Optional[str] = None
    value: Optional[str] = None
    attribute: Optional[str] = None

class XMLTestGenerator:
    def __init__(self, base_xml_path: str):
        self.base_xml_path = base_xml_path
        if not os.path.exists(self.base_xml_path):
            raise FileNotFoundError(f"Base XML file not found at {self.base_xml_path}")

    def generate(self, cases: List[TestCase], output_dir: str, prefix: str = ""):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"Generating {len(cases)} test cases in {output_dir}...")

        for case in cases:
            # Reload tree to ensure clean state for each test case
            tree = ET.parse(self.base_xml_path)
            root = tree.getroot()
            
            print(f"Generating: {case.name}")
            
            try:
                self._apply_action(root, case)
                
                filename = f"{prefix}_{case.name}.xml" if prefix else f"{case.name}.xml"
                output_path = os.path.join(output_dir, filename)
                tree.write(output_path, encoding='UTF-8', xml_declaration=True)
                
            except Exception as e:
                print(f"  ERROR generating {case.name}: {e}")

    def _apply_action(self, root: ET.Element, case: TestCase):
        if case.action == ActionType.SET_TEXT:
            self._set_text(root, case.xpath, case.value)
        elif case.action == ActionType.SET_ATTRIBUTE:
            self._set_attribute(root, case.xpath, case.attribute, case.value)
        elif case.action == ActionType.REMOVE_ELEMENT:
            self._remove_element(root, case.xpath)
        elif case.action == ActionType.CUSTOM_PI_EMAIL:
            self._custom_pi_email(root, case.value)
        elif case.action == ActionType.CUSTOM_PI_ORCID:
            self._custom_pi_orcid(root, case.value)
        elif case.action == ActionType.CUSTOM_REMOVE_PI:
            self._custom_remove_pi(root)
        elif case.action == ActionType.CUSTOM_PI_MISSING_NAME:
            self._custom_pi_missing_name(root)
        else:
            raise ValueError(f"Unknown action type: {case.action}")

    def _set_text(self, root: ET.Element, xpath: str, value: str):
        element = root.find(xpath, NAMESPACES)
        if element is not None:
            element.text = value
        else:
            print(f"  WARNING: Element not found at {xpath}")

    def _set_attribute(self, root: ET.Element, xpath: str, attribute: str, value: str):
        element = root.find(xpath, NAMESPACES)
        if element is not None:
            element.set(attribute, value)
        else:
            print(f"  WARNING: Element not found at {xpath}")

    def _remove_element(self, root: ET.Element, xpath: str):
        # Find parent and remove child
        # Strategy: find all potential parents based on the xpath structure
        if '/' not in xpath:
            return # Cannot remove root or invalid path
            
        parent_xpath, child_tag = xpath.rsplit('/', 1)
        
        # Handle namespace in child_tag
        if ':' in child_tag:
            prefix, tag = child_tag.split(':')
            expanded_tag = f"{{{NAMESPACES[prefix]}}}{tag}"
        else:
            expanded_tag = child_tag

        parents = root.findall(parent_xpath, NAMESPACES)
        for parent in parents:
            to_remove = [child for child in parent if child.tag == expanded_tag]
            for child in to_remove:
                parent.remove(child)

    def _custom_pi_email(self, root: ET.Element, value: str):
        parties = root.findall(".//cit:citedResponsibleParty", NAMESPACES)
        for party in parties:
            role = party.find(".//cit:role/cit:CI_RoleCode", NAMESPACES)
            if role is not None and role.get('codeListValue') == 'principalInvestigator':
                email = party.find(".//cit:electronicMailAddress/gco:CharacterString", NAMESPACES)
                if email is not None:
                    email.text = value

    def _custom_pi_orcid(self, root: ET.Element, value: str):
        parties = root.findall(".//cit:citedResponsibleParty", NAMESPACES)
        for party in parties:
            role = party.find(".//cit:role/cit:CI_RoleCode", NAMESPACES)
            if role is not None and role.get('codeListValue') == 'principalInvestigator':
                online_res = party.findall(".//cit:onlineResource/cit:CI_OnlineResource", NAMESPACES)
                for res in online_res:
                    name = res.find("cit:name/gco:CharacterString", NAMESPACES)
                    if name is not None and name.text in ('Orcid', 'Orchid'):
                        linkage = res.find("cit:linkage/gco:CharacterString", NAMESPACES)
                        if linkage is not None:
                            linkage.text = value

    def _custom_remove_pi(self, root: ET.Element):
        citations = root.findall(".//cit:CI_Citation", NAMESPACES)
        for citation in citations:
            to_remove = []
            for child in citation:
                if child.tag == f"{{{NAMESPACES['cit']}}}citedResponsibleParty":
                    role = child.find(".//cit:role/cit:CI_RoleCode", NAMESPACES)
                    if role is not None and role.get('codeListValue') == 'principalInvestigator':
                        to_remove.append(child)
            for child in to_remove:
                citation.remove(child)

    def _custom_pi_missing_name(self, root: ET.Element):
        parties = root.findall(".//cit:citedResponsibleParty", NAMESPACES)
        for party in parties:
            role = party.find(".//cit:role/cit:CI_RoleCode", NAMESPACES)
            if role is not None and role.get('codeListValue') == 'principalInvestigator':
                name_el = party.find(".//cit:individual/cit:CI_Individual/cit:name", NAMESPACES)
                if name_el is not None:
                    # Remove all children (like gco:CharacterString) to simulate missing name content
                    for child in list(name_el):
                        name_el.remove(child)

def get_invalid_test_cases() -> List[TestCase]:
    return [
        TestCase(
            name="title_empty",
            action=ActionType.SET_TEXT,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:citation/cit:CI_Citation/cit:title/gco:CharacterString",
            value="",
            description="Title must be non-empty string"
        ),
        TestCase(
            name="resource_type_invalid",
            action=ActionType.SET_ATTRIBUTE,
            xpath=".//mdb:metadataScope/mdb:MD_MetadataScope/mdb:resourceScope/mcc:MD_ScopeCode",
            attribute="codeListValue",
            value="Mosaic",
            description="Resource type cannot be Mosaic"
        ),
        TestCase(
            name="abstract_empty",
            action=ActionType.SET_TEXT,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:abstract/gco:CharacterString",
            value="",
            description="Abstract must be non-empty string"
        ),
        TestCase(
            name="purpose_invalid_format",
            action=ActionType.SET_TEXT,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:purpose/gco:CharacterString",
            value="InvalidPurpose",
            description="Purpose must be 'GRDC contract code, project title'"
        ),
        TestCase(
            name="contract_code_invalid",
            action=ActionType.SET_TEXT,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:purpose/gco:CharacterString",
            value="DAV1707-001-BLX1, title",
            description="Contract code is in format {A-Z}*3{0-9}*4-{0-9}*3-{A-Z}*3"
        ),
        TestCase(
            name="begin_date_empty",
            action=ActionType.SET_TEXT,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:extent/gex:EX_Extent/gex:temporalElement/gex:EX_TemporalExtent/gex:extent/gml:TimePeriod/gml:beginPosition",
            value="",
            description="Begin date non-empty"
        ),
        TestCase(
            name="begin_date_invalid_format",
            action=ActionType.SET_TEXT,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:extent/gex:EX_Extent/gex:temporalElement/gex:EX_TemporalExtent/gex:extent/gml:TimePeriod/gml:beginPosition",
            value="2022/06/15",
            description="Begin date dd-MM-YYYY format"
        ),
        TestCase(
            name="end_date_empty",
            action=ActionType.SET_TEXT,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:extent/gex:EX_Extent/gex:temporalElement/gex:EX_TemporalExtent/gex:extent/gml:TimePeriod/gml:endPosition",
            value="",
            description="End date non-empty"
        ),
        TestCase(
            name="end_date_invalid_format",
            action=ActionType.SET_TEXT,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:extent/gex:EX_Extent/gex:temporalElement/gex:EX_TemporalExtent/gex:extent/gml:TimePeriod/gml:endPosition",
            value="invalid",
            description="End date valid format"
        ),
        TestCase(
            name="spatial_ref_invalid",
            action=ActionType.SET_TEXT,
            xpath=".//mdb:referenceSystemInfo/mrs:MD_ReferenceSystem/mrs:referenceSystemIdentifier/mcc:MD_Identifier/mcc:code/gco:CharacterString",
            value="EPSG:9999",
            description="Reference system must be WGS84 or Google mercator"
        ),
        TestCase(
            name="west_longitude_non_float",
            action=ActionType.SET_TEXT,
            xpath=".//gex:westBoundLongitude/gco:Decimal",
            value="abc",
            description="WestBoundLongitude must be float"
        ),
        TestCase(
            name="east_longitude_non_float",
            action=ActionType.SET_TEXT,
            xpath=".//gex:eastBoundLongitude/gco:Decimal",
            value="abc",
            description="EastBoundLongitude must be float"
        ),
        TestCase(
            name="south_latitude_non_float",
            action=ActionType.SET_TEXT,
            xpath=".//gex:southBoundLatitude/gco:Decimal",
            value="abc",
            description="SouthBoundLatitude must be float"
        ),
        TestCase(
            name="north_latitude_non_float",
            action=ActionType.SET_TEXT,
            xpath=".//gex:northBoundLatitude/gco:Decimal",
            value="abc",
            description="NorthBoundLatitude must be float"
        ),
        TestCase(
            name="pi_invalid_email",
            action=ActionType.CUSTOM_PI_EMAIL,
            value="invalid-email",
            description="PI must have valid email"
        ),
        TestCase(
            name="pi_invalid_orcid",
            action=ActionType.CUSTOM_PI_ORCID,
            value="invalid-orcid",
            description="PI must have valid ORCID"
        ),
        TestCase(
            name="no_valid_identifier",
            action=ActionType.REMOVE_ELEMENT,
            xpath=".//mdb:distributionInfo/mrd:MD_Distribution/mrd:transferOptions/mrd:MD_DigitalTransferOptions/mrd:onLine/cit:CI_OnlineResource",
            description="Need one of Valid DOI, Handle, URL"
        ),
        TestCase(
            name="no_pi",
            action=ActionType.CUSTOM_REMOVE_PI,
            description="At least one principalInvestigator"
        ),
        TestCase(
            name="pi_missing_name",
            action=ActionType.CUSTOM_PI_MISSING_NAME,
            description="PI must have Given name and Family name"
        ),
        TestCase(
            name="classification_invalid",
            action=ActionType.SET_ATTRIBUTE,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:resourceConstraints/mco:MD_SecurityConstraints/mco:classification/mco:MD_ClassificationCode",
            attribute="codeListValue",
            value="invalid",
            description="Classification must be valid"
        ),
        TestCase(
            name="license_invalid",
            action=ActionType.SET_TEXT,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:resourceConstraints/mco:MD_LegalConstraints/mco:reference/cit:CI_Citation/cit:title/gco:CharacterString",
            value="Invalid License",
            description="License Type must be one of allowed list"
        )
    ]

def get_valid_test_cases() -> List[TestCase]:
    cases = []
    
    # Resource Types
    for res_type in ['dataset', 'product']:
        cases.append(TestCase(
            name=f"resource_type_{res_type}",
            action=ActionType.SET_ATTRIBUTE,
            xpath=".//mdb:metadataScope/mdb:MD_MetadataScope/mdb:resourceScope/mcc:MD_ScopeCode",
            attribute="codeListValue",
            value=res_type,
            description=f"Valid resource type: {res_type}"
        ))

    # Classifications
    classifications = [
        'unclassified', 'sensitive but unclassified',
        'for office use only', 'limited distribution',
        'restricted', 'confidential', 'protected', 'secret', 'top secret'
    ]
    for cls in classifications:
        safe_name = cls.replace(' ', '_')
        cases.append(TestCase(
            name=f"classification_{safe_name}",
            action=ActionType.SET_ATTRIBUTE,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:resourceConstraints/mco:MD_SecurityConstraints/mco:classification/mco:MD_ClassificationCode",
            attribute="codeListValue",
            value=cls,
            description=f"Valid classification: {cls}"
        ))

    # Spatial Data
    cases.append(TestCase(
        name="spatial_ref_google_mercator",
        action=ActionType.SET_TEXT,
        xpath=".//mdb:referenceSystemInfo/mrs:MD_ReferenceSystem/mrs:referenceSystemIdentifier/mcc:MD_Identifier/mcc:code/gco:CharacterString",
        value="Google mercator (EPSG:3857)",
        description="Valid spatial ref: Google mercator"
    ))

    # Licenses
    licenses = [
        'AVR transfer agreement',
        'Data access license agreement',
        'Creative commons attribution 4.0 (CC-BY)'
    ]
    for lic in licenses:
        safe_name = lic.replace(' ', '_').replace('(', '').replace(')', '').replace('.', '')
        cases.append(TestCase(
            name=f"license_{safe_name}",
            action=ActionType.SET_TEXT,
            xpath=".//mdb:identificationInfo/mri:MD_DataIdentification/mri:resourceConstraints/mco:MD_LegalConstraints/mco:reference/cit:CI_Citation/cit:title/gco:CharacterString",
            value=lic,
            description=f"Valid license: {lic}"
        ))
        
    return cases

def main():
    try:
        generator = XMLTestGenerator(VALID_XML_PATH)
        
        # Generate Invalid Cases
        invalid_cases = get_invalid_test_cases()
        generator.generate(invalid_cases, INVALID_OUTPUT_DIR, prefix="invalid")
        
        # Generate Valid Cases
        valid_cases = get_valid_test_cases()
        generator.generate(valid_cases, VALID_OUTPUT_DIR, prefix="valid")
        
        print("\nDone generating all test cases.")
        
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
