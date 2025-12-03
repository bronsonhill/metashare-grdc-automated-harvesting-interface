import os
import xml.etree.ElementTree as ET
import copy

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
OUTPUT_DIR = os.path.join(BASE_DIR, 'generated_invalid')

def get_xpath(path):
    """Helper to expand namespace prefixes in xpath"""
    parts = path.split('/')
    expanded_parts = []
    for part in parts:
        if ':' in part:
            prefix, tag = part.split(':')
            if prefix in NAMESPACES:
                expanded_parts.append(f"{{{NAMESPACES[prefix]}}}{tag}")
            else:
                expanded_parts.append(part)
        elif part == '': # Handle root //
            pass
        else:
            expanded_parts.append(part)
    
    # Reconstruct path. ET doesn't support full XPath 1.0, so we might need manual traversal for some things.
    # But for simple paths, we can use the expanded tag names or the prefix syntax if supported by find/findall with namespaces arg.
    # Actually, ET.find supports prefixes if we pass the namespaces dict.
    return path 

def generate_test_cases():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    tree = ET.parse(VALID_XML_PATH)
    root = tree.getroot()

    test_cases = [
        {
            "name": "title_empty",
            "action": "set_text",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:citation/cit:CI_Citation/cit:title/gco:CharacterString",
            "value": "",
            "description": "Title must be non-empty string"
        },
        {
            "name": "resource_type_invalid",
            "action": "set_attribute",
            "xpath": ".//mdb:metadataScope/mdb:MD_MetadataScope/mdb:resourceScope/mcc:MD_ScopeCode",
            "attribute": "codeListValue",
            "value": "Mosaic",
            "description": "Resource type cannot be Mosaic"
        },
        {
            "name": "abstract_empty",
            "action": "set_text",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:abstract/gco:CharacterString",
            "value": "",
            "description": "Abstract must be non-empty string"
        },
        {
            "name": "purpose_invalid_format",
            "action": "set_text",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:purpose/gco:CharacterString",
            "value": "InvalidPurpose",
            "description": "Purpose must be 'GRDC contract code, project title'"
        },
        {
            "name": "contract_code_invalid",
            "action": "set_text",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:purpose/gco:CharacterString",
            "value": "DAV1707-001-BLX1, title", # Invalid format
            "description": "Contract code is in format {A-Z}*3{0-9}*4-{0-9}*3-{A-Z}*3"
        },
        {
            "name": "begin_date_empty",
            "action": "set_text",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:extent/gex:EX_Extent/gex:temporalElement/gex:EX_TemporalExtent/gex:extent/gml:TimePeriod/gml:beginPosition",
            "value": "",
            "description": "Begin date non-empty"
        },
        {
            "name": "begin_date_invalid_format",
            "action": "set_text",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:extent/gex:EX_Extent/gex:temporalElement/gex:EX_TemporalExtent/gex:extent/gml:TimePeriod/gml:beginPosition",
            "value": "2022/06/15",
            "description": "Begin date dd-MM-YYYY format (ISO is usually YYYY-MM-DD, checking requirement)"
        },
        {
            "name": "end_date_empty",
            "action": "set_text",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:extent/gex:EX_Extent/gex:temporalElement/gex:EX_TemporalExtent/gex:extent/gml:TimePeriod/gml:endPosition",
            "value": "",
            "description": "End date non-empty"
        },
        {
            "name": "end_date_invalid_format",
            "action": "set_text",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:extent/gex:EX_Extent/gex:temporalElement/gex:EX_TemporalExtent/gex:extent/gml:TimePeriod/gml:endPosition",
            "value": "invalid",
            "description": "End date valid format"
        },
        {
            "name": "spatial_ref_invalid",
            "action": "set_text",
            "xpath": ".//mdb:referenceSystemInfo/mrs:MD_ReferenceSystem/mrs:referenceSystemIdentifier/mcc:MD_Identifier/mcc:code/gco:CharacterString",
            "value": "EPSG:9999",
            "description": "Reference system must be WGS84 or Google mercator"
        },
        {
            "name": "west_longitude_non_float",
            "action": "set_text",
            "xpath": ".//gex:westBoundLongitude/gco:Decimal",
            "value": "abc",
            "description": "WestBoundLongitude must be float"
        },
        {
            "name": "east_longitude_non_float",
            "action": "set_text",
            "xpath": ".//gex:eastBoundLongitude/gco:Decimal",
            "value": "abc",
            "description": "EastBoundLongitude must be float"
        },
        {
            "name": "south_latitude_non_float",
            "action": "set_text",
            "xpath": ".//gex:southBoundLatitude/gco:Decimal",
            "value": "abc",
            "description": "SouthBoundLatitude must be float"
        },
        {
            "name": "north_latitude_non_float",
            "action": "set_text",
            "xpath": ".//gex:northBoundLatitude/gco:Decimal",
            "value": "abc",
            "description": "NorthBoundLatitude must be float"
        },
        {
            "name": "pi_invalid_email",
            "action": "custom_pi_email",
            "value": "invalid-email",
            "description": "PI must have valid email"
        },
        {
            "name": "pi_invalid_orcid",
            "action": "custom_pi_orcid",
            "value": "invalid-orcid",
            "description": "PI must have valid ORCID"
        },
        {
            "name": "no_valid_identifier",
            "action": "remove_element",
            "xpath": ".//mdb:distributionInfo/mrd:MD_Distribution/mrd:transferOptions/mrd:MD_DigitalTransferOptions/mrd:onLine/cit:CI_OnlineResource",
            "description": "Need one of Valid DOI, Handle, URL"
        },
        {
            "name": "no_pi",
            "action": "custom_remove_pi",
            "description": "At least one principalInvestigator"
        },
        {
            "name": "pi_missing_name",
            "action": "custom_pi_missing_name",
            "description": "PI must have Given name and Family name (or just name string)"
        },
        {
            "name": "classification_invalid",
            "action": "set_attribute",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:resourceConstraints/mco:MD_SecurityConstraints/mco:classification/mco:MD_ClassificationCode",
            "attribute": "codeListValue",
            "value": "invalid",
            "description": "Classification must be valid"
        },
        {
            "name": "license_invalid",
            "action": "set_text",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:resourceConstraints/mco:MD_LegalConstraints/mco:reference/cit:CI_Citation/cit:title/gco:CharacterString",
            "value": "Invalid License",
            "description": "License Type must be one of allowed list"
        }
    ]

    print(f"Generating {len(test_cases)} test cases...")

    for case in test_cases:
        # Reload tree to ensure clean state
        tree = ET.parse(VALID_XML_PATH)
        root = tree.getroot()
        
        print(f"Generating: {case['name']}")
        
        try:
            if case['action'] == 'set_text':
                element = root.find(case['xpath'], NAMESPACES)
                if element is not None:
                    element.text = case['value']
                else:
                    print(f"  WARNING: Element not found for {case['name']} at {case['xpath']}")
            
            elif case['action'] == 'set_attribute':
                element = root.find(case['xpath'], NAMESPACES)
                if element is not None:
                    element.set(case['attribute'], case['value'])
                else:
                    print(f"  WARNING: Element not found for {case['name']} at {case['xpath']}")
            
            elif case['action'] == 'remove_element':
                # To remove, we need the parent. ET doesn't support parent lookup easily.
                # We'll do a search for parent.
                # XPath hack: find the element, then find parent. 
                # Actually, simpler to find all potential parents and check children.
                # For `no_valid_identifier`, parent is `mrd:onLine`.
                target_xpath = case['xpath']
                parent_xpath = target_xpath.rsplit('/', 1)[0]
                child_tag = target_xpath.rsplit('/', 1)[1]
                
                # Expand namespace for tag matching if needed, but findall with namespaces works well
                parents = root.findall(parent_xpath, NAMESPACES)
                for parent in parents:
                    # Find child to remove
                    # We need to handle the namespace in child_tag for find
                    child = parent.find(child_tag.replace('cit:', 'cit:').replace('mrd:', 'mrd:'), NAMESPACES) # simplified
                    # Better: just use the full xpath logic or iterate children
                    
                    # Let's iterate children and remove if tag matches
                    # We need the expanded tag name for the child
                    prefix, tag = child_tag.split(':')
                    expanded_tag = f"{{{NAMESPACES[prefix]}}}{tag}"
                    
                    to_remove = []
                    for child in parent:
                        if child.tag == expanded_tag:
                            to_remove.append(child)
                    
                    for child in to_remove:
                        parent.remove(child)

            elif case['action'] == 'custom_pi_email':
                # Find all PIs
                parties = root.findall(".//cit:citedResponsibleParty", NAMESPACES)
                for party in parties:
                    role = party.find(".//cit:role/cit:CI_RoleCode", NAMESPACES)
                    if role is not None and role.get('codeListValue') == 'principalInvestigator':
                        email = party.find(".//cit:electronicMailAddress/gco:CharacterString", NAMESPACES)
                        if email is not None:
                            email.text = case['value']
            
            elif case['action'] == 'custom_pi_orcid':
                parties = root.findall(".//cit:citedResponsibleParty", NAMESPACES)
                for party in parties:
                    role = party.find(".//cit:role/cit:CI_RoleCode", NAMESPACES)
                    if role is not None and role.get('codeListValue') == 'principalInvestigator':
                        # Find ORCID link
                        online_res = party.findall(".//cit:onlineResource/cit:CI_OnlineResource", NAMESPACES)
                        for res in online_res:
                            name = res.find("cit:name/gco:CharacterString", NAMESPACES)
                            if name is not None and (name.text == 'Orcid' or name.text == 'Orchid'):
                                linkage = res.find("cit:linkage/gco:CharacterString", NAMESPACES)
                                if linkage is not None:
                                    linkage.text = case['value']

            elif case['action'] == 'custom_remove_pi':
                # Find parent of citedResponsibleParty -> identificationInfo/MD_DataIdentification/citation/CI_Citation
                # We need to iterate over citation elements and remove parties that are PI
                citations = root.findall(".//cit:CI_Citation", NAMESPACES)
                for citation in citations:
                    to_remove = []
                    for child in citation:
                        # Check if child is citedResponsibleParty
                        if child.tag == f"{{{NAMESPACES['cit']}}}citedResponsibleParty":
                            role = child.find(".//cit:role/cit:CI_RoleCode", NAMESPACES)
                            if role is not None and role.get('codeListValue') == 'principalInvestigator':
                                to_remove.append(child)
                    for child in to_remove:
                        citation.remove(child)

            elif case['action'] == 'custom_pi_missing_name':
                parties = root.findall(".//cit:citedResponsibleParty", NAMESPACES)
                for party in parties:
                    role = party.find(".//cit:role/cit:CI_RoleCode", NAMESPACES)
                    if role is not None and role.get('codeListValue') == 'principalInvestigator':
                        name_el = party.find(".//cit:individual/cit:CI_Individual/cit:name", NAMESPACES)
                        if name_el is not None:
                            # Remove the gco:CharacterString inside or the name element itself
                            # Let's remove the name element content
                            for child in list(name_el):
                                name_el.remove(child)

            # Save
            output_path = os.path.join(OUTPUT_DIR, f"invalid_{case['name']}.xml")
            tree.write(output_path, encoding='UTF-8', xml_declaration=True)
            
        except Exception as e:
            print(f"  ERROR generating {case['name']}: {e}")

    # --- Valid Test Cases ---
    VALID_OUTPUT_DIR = os.path.join(BASE_DIR, 'generated_valid')
    if not os.path.exists(VALID_OUTPUT_DIR):
        os.makedirs(VALID_OUTPUT_DIR)

    valid_cases = []
    
    # Resource Types
    for res_type in ['dataset', 'product']:
        valid_cases.append({
            "name": f"resource_type_{res_type}",
            "action": "set_attribute",
            "xpath": ".//mdb:metadataScope/mdb:MD_MetadataScope/mdb:resourceScope/mcc:MD_ScopeCode",
            "attribute": "codeListValue",
            "value": res_type,
            "description": f"Valid resource type: {res_type}"
        })

    # Classifications
    classifications = [
        'unclassified', 'sensitive but unclassified',
        'for office use only', 'limited distribution',
        'restricted', 'confidential', 'protected', 'secret', 'top secret'
    ]
    for cls in classifications:
        # Create a safe filename
        safe_name = cls.replace(' ', '_')
        valid_cases.append({
            "name": f"classification_{safe_name}",
            "action": "set_attribute",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:resourceConstraints/mco:MD_SecurityConstraints/mco:classification/mco:MD_ClassificationCode",
            "attribute": "codeListValue",
            "value": cls,
            "description": f"Valid classification: {cls}"
        })

    # Spatial Data
    valid_cases.append({
        "name": "spatial_ref_google_mercator",
        "action": "set_text",
        "xpath": ".//mdb:referenceSystemInfo/mrs:MD_ReferenceSystem/mrs:referenceSystemIdentifier/mcc:MD_Identifier/mcc:code/gco:CharacterString",
        "value": "Google mercator (EPSG:3857)",
        "description": "Valid spatial ref: Google mercator"
    })

    # Licenses
    licenses = [
        'AVR transfer agreement',
        'Data access license agreement',
        'Creative commons attribution 4.0 (CC-BY)'
    ]
    for lic in licenses:
        safe_name = lic.replace(' ', '_').replace('(', '').replace(')', '').replace('.', '')
        valid_cases.append({
            "name": f"license_{safe_name}",
            "action": "set_text",
            "xpath": ".//mdb:identificationInfo/mri:MD_DataIdentification/mri:resourceConstraints/mco:MD_LegalConstraints/mco:reference/cit:CI_Citation/cit:title/gco:CharacterString",
            "value": lic,
            "description": f"Valid license: {lic}"
        })

    print(f"Generating {len(valid_cases)} valid test cases...")

    for case in valid_cases:
        tree = ET.parse(VALID_XML_PATH)
        root = tree.getroot()
        
        print(f"Generating: {case['name']}")
        
        try:
            if case['action'] == 'set_attribute':
                element = root.find(case['xpath'], NAMESPACES)
                if element is not None:
                    element.set(case['attribute'], case['value'])
                else:
                    print(f"  WARNING: Element not found for {case['name']} at {case['xpath']}")
            
            elif case['action'] == 'set_text':
                element = root.find(case['xpath'], NAMESPACES)
                if element is not None:
                    element.text = case['value']
                else:
                    print(f"  WARNING: Element not found for {case['name']} at {case['xpath']}")

            output_path = os.path.join(VALID_OUTPUT_DIR, f"valid_{case['name']}.xml")
            tree.write(output_path, encoding='UTF-8', xml_declaration=True)
            
        except Exception as e:
            print(f"  ERROR generating {case['name']}: {e}")

if __name__ == "__main__":
    generate_test_cases()
