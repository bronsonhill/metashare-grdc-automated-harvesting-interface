from connector import ConnectorInterface, GeoNetworkConnector, ConnectorError
from validator import GeoNetworkValidator
from notifications import NotificationService, FileNotificationBackend, BatchStats, InvalidRecordDetails
from config import ConfigLoader
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET


class BatchJob:
    def __init__(self, connector: ConnectorInterface, notifications: NotificationService):
        self.connector = connector
        self.validator = GeoNetworkValidator()
        self.notifications = notifications

        self.connection_success = False
        self.search_hits = []
        self.since = self._set_since()
        self.config_loader = ConfigLoader()
        self.base_url = self.config_loader.source_config.url

        
    def run(self):
        start_time = datetime.now()
        self._get_delta_records()
        self._log_state()
        
        valid_count = 0
        invalid_records = []
        
        for record in self.search_hits:
            is_valid, error_details = self._validate_record(record)
            if is_valid:
                valid_count += 1
            else:
                invalid_records.append(error_details)
                self.notifications.notify_record_processor_error(error_details, "placeholder@example.com")

        end_time = datetime.now()
        
        stats = BatchStats(
            total_records=len(self.search_hits),
            valid_count=valid_count,
            invalid_count=len(invalid_records),
            start_time=start_time,
            end_time=end_time
        )
        
        self.notifications.notify_batch_summary(stats, invalid_records)

        
    def _get_delta_records(self):
        self.connection_success = self.connector.can_connect()
        if not self.connection_success:
            self.notifications.notify_connection_error("Failed to connect to GeoNetwork.")
            return []

        try:
            query = self.connector.construct_query(self.since)
            self.search_hits = self.connector.search_records(query)
        except ConnectorError as e:
            self.notifications.notify_connection_error(str(e))
        except Exception as e:
            # Handle unexpected errors
            print(f"Unexpected error during search: {e}")
            self.notifications.notify_connection_error(f"Unexpected error: {e}")
        return self.search_hits

    def _set_since(self):
        # temporary implementation - should retrieve state from database
        return datetime.now(timezone.utc) - timedelta(days=30)

    def _log_state(self):
        print(f"Connection success: {self.connection_success}")
        print(f"Search hits: {len(self.search_hits)}")

    def _validate_record(self, record) -> tuple[bool, InvalidRecordDetails | None]:
        result = self.validator.validate(record)
        if result.is_valid:
            return True, None
        
        # Parse record for extraction
        try:
            record_element = ET.fromstring(record)
        except ET.ParseError:
            return False, InvalidRecordDetails("Unknown", "Unknown", "Unknown", ["XML Parse Error"], "")

        record_id = self._extract_id(record_element)
        processor_name = self._extract_processor_name(record_element)
        
        base = self.base_url.rstrip('/')
        if base.endswith("/geonetwork/srv/api"):
            base = base.replace("/geonetwork/srv/api", "")
        
        record_link = f"{base}/geonetwork/srv/eng/catalog.search#/metadata/{record_id}"

        details = InvalidRecordDetails(
            record_id=record_id,
            processor_name=processor_name,
            errors=result.errors,
            record_link=record_link
        )
        return False, details

    def _extract_id(self, record) -> str:
        node = record.find("mdb:metadataIdentifier/mcc:MD_Identifier/mcc:code/gco:CharacterString", self.config_loader.namespaces)
        if node is not None and node.text:
             return node.text
        return "Unknown_ID"

    def _extract_processor_name(self, record) -> str:
        # Look for contacts with role 'processor'
        for contact in record.findall(".//mdb:contact/cit:CI_Responsibility", self.config_loader.namespaces):
            role_code = contact.find("cit:role/cit:CI_RoleCode", self.config_loader.namespaces)
            if role_code is not None and role_code.get("codeListValue") == "processor":
                # Try to find individual name
                name_node = contact.find("cit:party/cit:CI_Organisation/cit:individual/cit:CI_Individual/cit:name/gco:CharacterString", self.config_loader.namespaces)
                if name_node is not None and name_node.text:
                    return name_node.text
                
                # Fallback to organisation name if individual not found
                org_node = contact.find("cit:party/cit:CI_Organisation/cit:name/gco:CharacterString", self.config_loader.namespaces)
                if org_node is not None and org_node.text:
                    return org_node.text
        
        
        

                    
        return "Unknown Processor"

        


if __name__ == "__main__":
    config_loader = ConfigLoader("config/config_dev.toml")
    
    notifications_backend = FileNotificationBackend()
    notifications = NotificationService(notifications_backend)
    batch_job = BatchJob(GeoNetworkConnector(), notifications)
    batch_job.run()