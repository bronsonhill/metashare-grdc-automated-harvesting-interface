from connector import ConnectorInterface, GeoNetworkConnector 
from validator import GeoNetworkValidator
from notifications import NotificationService, FileNotificationBackend
from config import ConfigLoader
from datetime import datetime, timezone, timedelta

class BatchJob:
    def __init__(self, connector: ConnectorInterface, notifications: NotificationService):
        self.connector = connector
        self.validator = GeoNetworkValidator()
        self.notifications = notifications

        self.connection_success = False
        self.search_hits = []
        self.since = self._set_since()
        
    def run(self):
        self._get_delta_records()
        self._log_state()
        self._validate_records()
        
    def _get_delta_records(self):
        self.connection_success = self.connector.can_connect()
        try:
            query = self.connector.construct_query(self.since)
            self.search_hits = self.connector.search_records(query)
        except Exception as e:
            self.notifications.notify_connection_error(e)
        return self.search_hits

    def _set_since(self):
        # temporary implementation - should retrieve state from database
        return datetime.now(timezone.utc) - timedelta(days=7)

    def _log_state(self):
        print(f"Connection success: {self.connection_success}")
        print(f"Search hits: {len(self.search_hits)}")

    def _validate_records(self):
        for record in self.search_hits:
            result = self.validator.validate(record)
            print(result.errors)
            if not result.is_valid:
                self.notifications.notify_validation_error(result.errors)
        


if __name__ == "__main__":
    config_loader = ConfigLoader("config/config_dev.toml")
    
    notifications_backend = FileNotificationBackend()
    notifications = NotificationService(notifications_backend)
    batch_job = BatchJob(GeoNetworkConnector(), notifications)
    batch_job.run()