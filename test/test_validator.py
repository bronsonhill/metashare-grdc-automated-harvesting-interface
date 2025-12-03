import unittest
from validator.validator import GeoNetworkValidator
from validator.rules import CheckFieldExists

class TestGeoNetworkValidator(unittest.TestCase):
    def setUp(self):
        self.rules = [
            CheckFieldExists(".//cit:title/gco:CharacterString", "title"),
            CheckFieldExists(".//mri:abstract/gco:CharacterString", "abstract")
        ]
        self.validator = GeoNetworkValidator(self.rules)

    def test_valid_record(self):
        xml = """
        <mdb:MD_Metadata xmlns:mdb="http://standards.iso.org/iso/19115/-3/mdb/2.0" 
                         xmlns:cit="http://standards.iso.org/iso/19115/-3/cit/2.0" 
                         xmlns:gco="http://standards.iso.org/iso/19115/-3/gco/1.0" 
                         xmlns:mri="http://standards.iso.org/iso/19115/-3/mri/1.0">
            <mdb:identificationInfo>
                <mri:MD_DataIdentification>
                    <mri:citation>
                        <cit:CI_Citation>
                            <cit:title>
                                <gco:CharacterString>Valid Title</gco:CharacterString>
                            </cit:title>
                        </cit:CI_Citation>
                    </mri:citation>
                    <mri:abstract>
                        <gco:CharacterString>Valid Abstract</gco:CharacterString>
                    </mri:abstract>
                </mri:MD_DataIdentification>
            </mdb:identificationInfo>
        </mdb:MD_Metadata>
        """
        result = self.validator.validate(xml)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

    def test_missing_title(self):
        xml = """
        <mdb:MD_Metadata xmlns:mdb="http://standards.iso.org/iso/19115/-3/mdb/2.0" 
                         xmlns:cit="http://standards.iso.org/iso/19115/-3/cit/2.0" 
                         xmlns:gco="http://standards.iso.org/iso/19115/-3/gco/1.0" 
                         xmlns:mri="http://standards.iso.org/iso/19115/-3/mri/1.0">
            <mdb:identificationInfo>
                <mri:MD_DataIdentification>
                    <mri:citation>
                        <cit:CI_Citation>
                            <!-- Missing Title -->
                        </cit:CI_Citation>
                    </mri:citation>
                    <mri:abstract>
                        <gco:CharacterString>Valid Abstract</gco:CharacterString>
                    </mri:abstract>
                </mri:MD_DataIdentification>
            </mdb:identificationInfo>
        </mdb:MD_Metadata>
        """
        result = self.validator.validate(xml)
        self.assertFalse(result.is_valid)
        self.assertIn("Record is missing a title.", result.errors)

    def test_missing_abstract(self):
        xml = """
        <mdb:MD_Metadata xmlns:mdb="http://standards.iso.org/iso/19115/-3/mdb/2.0" 
                         xmlns:cit="http://standards.iso.org/iso/19115/-3/cit/2.0" 
                         xmlns:gco="http://standards.iso.org/iso/19115/-3/gco/1.0" 
                         xmlns:mri="http://standards.iso.org/iso/19115/-3/mri/1.0">
            <mdb:identificationInfo>
                <mri:MD_DataIdentification>
                    <mri:citation>
                        <cit:CI_Citation>
                            <cit:title>
                                <gco:CharacterString>Valid Title</gco:CharacterString>
                            </cit:title>
                        </cit:CI_Citation>
                    </mri:citation>
                    <!-- Missing Abstract -->
                </mri:MD_DataIdentification>
            </mdb:identificationInfo>
        </mdb:MD_Metadata>
        """
        result = self.validator.validate(xml)
        self.assertFalse(result.is_valid)
        self.assertIn("Record is missing a abstract.", result.errors)

    def test_multiple_errors(self):
        xml = """
        <mdb:MD_Metadata xmlns:mdb="http://standards.iso.org/iso/19115/-3/mdb/2.0" 
                         xmlns:cit="http://standards.iso.org/iso/19115/-3/cit/2.0" 
                         xmlns:gco="http://standards.iso.org/iso/19115/-3/gco/1.0" 
                         xmlns:mri="http://standards.iso.org/iso/19115/-3/mri/1.0">
            <mdb:identificationInfo>
                <mri:MD_DataIdentification>
                    <mri:citation>
                        <cit:CI_Citation>
                            <!-- Missing Title -->
                        </cit:CI_Citation>
                    </mri:citation>
                    <!-- Missing Abstract -->
                </mri:MD_DataIdentification>
            </mdb:identificationInfo>
        </mdb:MD_Metadata>
        """
        result = self.validator.validate(xml)
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)
        self.assertIn("Record is missing a title.", result.errors)
        self.assertIn("Record is missing a abstract.", result.errors)

if __name__ == '__main__':
    unittest.main()
