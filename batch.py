from connector import ConnectorInterface, GeoNetworkConnector 
from notifications import NotificationService, FileNotificationBackend
from config_loader import ConfigLoader

class BatchJob:
    def __init__(self, connector: ConnectorInterface, notifications: NotificationService):
        self.connector = connector
        self.notifications = notifications

        self.connection_success = False
        self.search_hits = []
        self.since = self._get_since()
        
    def run(self):
        self.connection_success = self.connector.can_connect()
        try:
            self.search_hits = self.connector.search()
        except Exception as e:
            self.notifications.notify_connection_error(e)

    def _get_since(self):
        # temporary; will retrieve state from database
        return datetime.now(timezone.utc) - timedelta(days=7)


if __name__ == "__main__":
    config_loader = ConfigLoader("config_dev.toml")
    source_config = config_loader.get_source_config()
    notifications_config = config_loader.get_notifications_config()
    connector = GeoNetworkConnector(source_config)
    notifications_backend = FileNotificationBackend()
    notifications = NotificationService(notifications_config, notifications_backend)
    batch_job = BatchJob(connector, notifications)
    batch_job.run()