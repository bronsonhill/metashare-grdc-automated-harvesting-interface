import unittest
import os
import sys

# Add parent directory to path to allow importing validator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from validator.validator import GeoNetworkValidator

class TestGeoNetworkValidatorXML(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from config import ConfigLoader
        ConfigLoader("config/config_dev.toml")
        cls.validator = GeoNetworkValidator()
        cls.base_path = os.path.dirname(os.path.abspath(__file__))
        cls.valid_data_path = os.path.join(cls.base_path, 'data/geonetwork/generated_valid')
        cls.invalid_data_path = os.path.join(cls.base_path, 'data/geonetwork/generated_invalid')

def create_test_function(filepath, should_be_valid):
    def test(self):
        with open(filepath, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        result = self.validator.validate(xml_content)
        if should_be_valid:
            self.assertTrue(result.is_valid, f"File {os.path.basename(filepath)} should be valid but failed with errors: {result.errors}")
        else:
            self.assertFalse(result.is_valid, f"File {os.path.basename(filepath)} should be invalid but passed validation.")
    return test

# Dynamically add test methods to the class
base_path = os.path.dirname(os.path.abspath(__file__))
valid_data_path = os.path.join(base_path, 'data/geonetwork/generated_valid')
invalid_data_path = os.path.join(base_path, 'data/geonetwork/generated_invalid')

if os.path.exists(valid_data_path):
    for filename in os.listdir(valid_data_path):
        if filename.endswith(".xml"):
            test_name = f"test_valid_{filename.replace('.', '_').replace('-', '_')}"
            test_func = create_test_function(os.path.join(valid_data_path, filename), True)
            setattr(TestGeoNetworkValidatorXML, test_name, test_func)

if os.path.exists(invalid_data_path):
    for filename in os.listdir(invalid_data_path):
        if filename.endswith(".xml"):
            test_name = f"test_invalid_{filename.replace('.', '_').replace('-', '_')}"
            test_func = create_test_function(os.path.join(invalid_data_path, filename), False)
            setattr(TestGeoNetworkValidatorXML, test_name, test_func)

if __name__ == '__main__':
    unittest.main()
