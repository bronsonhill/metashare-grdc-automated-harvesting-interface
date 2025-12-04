import tomllib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class SourceConfig:
    url: str
    search_endpoint: str
    get_record_endpoint: str
    test_endpoint: str
    maxRecords: int = 100
    grdc_filter_keywords: List[str] = field(default_factory=list)

@dataclass
class NotificationsConfig:
    channel: str
    destination: List[str]
    client_id: str
    client_secret: str

@dataclass
class RuleConfig:
    type: str
    xpath: str
    field_display_name: str
    allowed_values: List[str] = field(default_factory=list)

@dataclass
class ValidatorConfig:
    rules: List[RuleConfig]

class ConfigLoader:
    _instance = None
    _initialized = False

    def __new__(cls, config_path: str = "config/config.toml"):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = "config/config.toml"):
        if not self._initialized:
            self.config_path = config_path
            self._config = self._load_config()
            self.source_config = self._load_source_config()
            self.notifications_config = self._load_notifications_config()
            self.validator_config = self._load_validator_config()
            self._initialized = True

    def _load_config(self) -> Dict[str, Any]:
        with open(self.config_path, "rb") as f:
            return tomllib.load(f)

    def _load_source_config(self) -> SourceConfig:
        connect_section = self._config.get("source", {})
        return SourceConfig(
            url=connect_section.get("url", ""),
            search_endpoint=connect_section.get("search_endpoint", ""),
            get_record_endpoint=connect_section.get("get_record_endpoint", ""),
            maxRecords=connect_section.get("maxRecords", 100),
            test_endpoint=connect_section.get("test_endpoint", ""),
            grdc_filter_keywords=connect_section.get("grdc_filter_keywords", [])
        )
    
    def _load_notifications_config(self) -> NotificationsConfig:
        notifications_section = self._config.get("notifications", {})
        return NotificationsConfig(
            channel=notifications_section.get("channel", "email"),
            destination=notifications_section.get("destination", []),
            client_id=notifications_section.get("client_id", ""),
            client_secret=notifications_section.get("client_secret", "")
        )

    def _load_validator_config(self) -> ValidatorConfig:
        rules_data = self._config.get("rules", [])
        rules = []
        for r in rules_data:
            rules.append(RuleConfig(
                type=r.get("type", ""),
                xpath=r.get("path", ""),
                field_display_name=r.get("field_display_name", ""),
                allowed_values=r.get("allowed_values", [])
            ))

        return ValidatorConfig(
            rules=rules
        )
    