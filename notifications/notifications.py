from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional
import os
import datetime
from config import NotificationsConfig, ConfigLoader


@dataclass
class NotificationMessage:
    subject: str
    content: str
    channel: Optional[str] = None  # Optional override


class NotificationBackend(ABC):
    @abstractmethod
    def send(self, message: NotificationMessage, config: NotificationsConfig):
        pass


class FileNotificationBackend(NotificationBackend):
    def __init__(self, output_dir: str = "test/stub_notifications"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def send(self, message: NotificationMessage, config: NotificationsConfig):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize subject for filename
        safe_subject = "".join([c if c.isalnum() else "_" for c in message.subject])
        filename = f"{timestamp}_{safe_subject}.txt"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w") as f:
            f.write(f"Subject: {message.subject}\n")
            f.write(f"Channel: {message.channel or config.channel}\n")
            f.write(f"Destination: {config.destination}\n")
            f.write("-" * 20 + "\n")
            f.write(message.content)
            f.write("\n")


class EmailNotificationMicrosoftBackend(NotificationBackend):
    def send(self, message: NotificationMessage, config: NotificationsConfig):
        # Placeholder for email implementation
        print(f"Sending email: {message.subject} to {config.destination}")


class NotificationService:
    def __init__(self, backend: NotificationBackend):
        self.config = ConfigLoader().notifications_config
        self.backend = backend

    def notify_connection_error(self, error_message: str):
        msg = NotificationMessage(
            subject="Connection Error",
            content=f"A connection error occurred: {error_message}"
        )
        self.backend.send(msg, self.config)

    def notify_invalid_metashare_record(self, record_id: str, details: str):
        msg = NotificationMessage(
            subject=f"Invalid Metashare Record: {record_id}",
            content=f"Record {record_id} is invalid. Details: {details}"
        )
        self.backend.send(msg, self.config)

    def notify_batch_job_status(self, job_id: str, status: str):
        msg = NotificationMessage(
            subject=f"Batch Job Status: {job_id}",
            content=f"Job {job_id} is now {status}."
        )
        self.backend.send(msg, self.config)

    def notify_grdc_harvest(self, record_count: int, status: str):
        msg = NotificationMessage(
            subject="GRDC Harvest Update",
            content=f"Harvest completed. Status: {status}. Records processed: {record_count}"
        )
        self.backend.send(msg, self.config)

    def notify_validation_error(self, errors: list[str]):
        msg = NotificationMessage(
            subject="Validation Error",
            content=f"Validation failed with errors: {', '.join(errors)}"
        )
        self.backend.send(msg, self.config)
