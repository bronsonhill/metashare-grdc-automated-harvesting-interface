import tomllib
from typing import Any, Dict, List
from dataclasses import dataclass, field

@dataclass
class SourceConfig:
    url: str
    search_endpoint: str
    maxRecords: int = 100
    grdc_filter_keywords: List[str] = field(default_factory=list)


@dataclass
class NotificationsConfig:
    channel: str
    destination: List[str]
    client_id: str
    client_secret: str
    

class ConfigLoader:
    def __init__(self, config_path: str = "config.toml"):
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        with open(self.config_path, "rb") as f:
            return tomllib.load(f)

    def get_source_config(self) -> SourceConfig:
        connect_section = self._config.get("source", {})
        return SourceConfig(
            url=connect_section.get("url", ""),
            search_endpoint=connect_section.get("search_endpoint", ""),
            maxRecords=connect_section.get("maxRecords", 100),
            grdc_filter_keywords=connect_section.get("grdc_filter_keywords", [])
        )
    
    def get_notifications_config(self) -> NotificationsConfig:
        notifications_section = self._config.get("notifications", {})
        return NotificationsConfig(
            channel=notifications_section.get("channel", "email"),
            destination=notifications_section.get("destination", []),
            client_id=notifications_section.get("client_id", ""),
            client_secret=notifications_section.get("client_secret", "")
        )