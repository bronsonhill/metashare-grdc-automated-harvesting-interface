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
    recipient: Optional[str] = None  # Optional recipient override


@dataclass
class InvalidRecordDetails:
    record_id: str
    processor_name: str
    errors: list[str]
    record_link: str


@dataclass
class BatchStats:
    total_records: int
    valid_count: int
    invalid_count: int
    start_time: datetime.datetime
    end_time: datetime.datetime



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
            f.write(f"Destination: {message.recipient or config.destination}\n")
            f.write("-" * 20 + "\n")
            f.write(message.content)
            f.write("\n")


class EmailNotificationMicrosoftBackend(NotificationBackend):
    def send(self, message: NotificationMessage, config: NotificationsConfig):
        # Placeholder for email implementation
        destination = message.recipient or config.destination
        print(f"Sending email: {message.subject} to {destination}")


class NotificationService:
    def __init__(self, backend: NotificationBackend):
        self.config = ConfigLoader().notifications_config
        self.backend = backend

    def notify_connection_error(self, error_message: str):
        msg = NotificationMessage(
            subject="Connection Error",
            content=f"Establishing a basic connection to the Metashare/GeoNetwork API has failed. The connection attempt may have failed due to Metashare/GeoNetwork being down or unreachable. The Batch Job will still be attempted, but may fail.\n\nError: {error_message}"
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
        # Deprecated in favor of notify_record_processor_error for individual records
        # Keeping for backward compatibility if needed, or can be removed
        msg = NotificationMessage(
            subject="Metashare Record Invalid",
            content=f"It has been detected that a metashare record is invalid, and therefore it cannot be processed.\n\nErrors detected: {', '.join(errors)}"
        )
        self.backend.send(msg, self.config)

    def notify_batch_summary(self, stats: BatchStats, invalid_records: list[InvalidRecordDetails]):
        content = f"Batch Summary:\n"
        content += f"Total Records Processed: {stats.total_records}\n"
        content += f"Valid Records: {stats.valid_count}\n"
        content += f"Invalid Records: {stats.invalid_count}\n"
        content += f"Duration: {stats.end_time - stats.start_time}\n"
        
        if invalid_records:
            content += "\nInvalid Records Details:\n"
            content += "-" * 20 + "\n"
            for record in invalid_records:
                content += f"Record ID: {record.record_id}\n"
                content += f"Processor: {record.processor_name}\n"
                content += f"Link: {record.record_link}\n"
                content += f"Errors:\n"
                for error in record.errors:
                    content += f"  - {error}\n"
                content += "-" * 10 + "\n"
        else:
            content += "\nNo invalid records found.\n"

        msg = NotificationMessage(
            subject=f"Batch Process Summary - {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            content=content
        )
        self.backend.send(msg, self.config)

    def notify_record_processor_error(self, record: InvalidRecordDetails, recipient_email: str):
        content = f"Dear {record.processor_name},\n\n"
        content += f"The following metadata record has failed validation:\n"
        content += f"Record ID: {record.record_id}\n"
        content += f"Link: {record.record_link}\n"
        content += f"\nErrors:\n"
        for error in record.errors:
            content += f" - {error}\n"
        content += "\nPlease correct these issues in Metashare.\n"

        msg = NotificationMessage(
            subject=f"Action Required: Invalid Metadata Record {record.record_id}",
            content=content,
            recipient=recipient_email
        )
        self.backend.send(msg, self.config)

