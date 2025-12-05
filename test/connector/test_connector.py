import unittest
from unittest.mock import MagicMock, patch
import requests
from connector import GeoNetworkConnector, ConnectorError

class TestGeoNetworkConnector(unittest.TestCase):
    def setUp(self):
        # Patch ConfigLoader to avoid reading actual config files
        self.config_loader_patcher = patch('connector.connector.ConfigLoader')
        self.mock_config_loader_class = self.config_loader_patcher.start()
        
        # Setup mock config
        self.mock_source_config = MagicMock()
        self.mock_source_config.url = "http://example.com/geonetwork"
        self.mock_source_config.search_endpoint = "/srv/api/search"
        self.mock_source_config.test_endpoint = "/srv/api/status"
        self.mock_source_config.get_record_endpoint = "/srv/api/records"
        self.mock_source_config.maxRecords = 10
        self.mock_source_config.grdc_filter_keywords = ["GRDC", "Grains"]
        
        self.mock_config_loader_instance = self.mock_config_loader_class.return_value
        self.mock_config_loader_instance.source_config = self.mock_source_config

        # Initialize connector
        self.connector = GeoNetworkConnector()
        # Mock the requests session
        self.connector.session = MagicMock()

    def tearDown(self):
        self.config_loader_patcher.stop()

    def test_can_connect_success(self):
        """Test successful connection to GeoNetwork."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        self.connector.session.get.return_value = mock_response

        self.assertTrue(self.connector.can_connect())
        self.connector.session.get.assert_called_with("http://example.com/geonetwork/srv/api/status")

    def test_can_connect_failure(self):
        """Test failed connection to GeoNetwork."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Connection error")
        self.connector.session.get.return_value = mock_response

        self.assertFalse(self.connector.can_connect())

    def test_get_record_success(self):
        """Test retrieving a single record successfully."""
        uuid = "test-uuid-123"
        expected_xml = "<xml>Record Content</xml>"
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = expected_xml
        self.connector.session.get.return_value = mock_response

        result = self.connector.get_record(uuid)
        
        self.assertEqual(result, expected_xml)
        self.connector.session.get.assert_called_with("http://example.com/geonetwork/srv/api/records/test-uuid-123")
        # Check if Accept header was updated
        self.connector.session.headers.update.assert_called_with({"Accept": "application/xml"})

    def test_get_record_failure(self):
        """Test failure when retrieving a record."""
        uuid = "invalid-uuid"
        
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        self.connector.session.get.return_value = mock_response

        with self.assertRaises(ConnectorError) as context:
            self.connector.get_record(uuid)
        
        self.assertIn("Error getting record invalid-uuid", str(context.exception))

    @patch('connector.connector.GeoNetworkConnector._search_records_json')
    @patch('connector.connector.GeoNetworkConnector._get_records_xml')
    def test_search_records(self, mock_get_xml, mock_search_json):
        """Test the high-level search_records flow."""
        query = {"some": "query"}
        
        # Setup mock returns
        mock_search_json.return_value = [
            {'_source': {'uuid': 'uuid1'}},
            {'_source': {'uuid': 'uuid2'}}
        ]
        mock_get_xml.return_value = ["<xml>1</xml>", "<xml>2</xml>"]

        # Execute
        results = self.connector.search_records(query)

        # Verify
        self.assertEqual(len(results), 2)
        self.assertEqual(results, ["<xml>1</xml>", "<xml>2</xml>"])
        
        # Verify calls
        mock_search_json.assert_called_with(query)
        mock_get_xml.assert_called_with(['uuid1', 'uuid2'])
        self.connector.session.headers.update.assert_called_with({"Accept": "application/xml"})

if __name__ == '__main__':
    unittest.main()
