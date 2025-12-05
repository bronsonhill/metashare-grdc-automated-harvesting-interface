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

    @property
    def namespaces(self) -> Dict[str, str]:
        return {
            'mdb': 'http://standards.iso.org/iso/19115/-3/mdb/2.0',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'cat': 'http://standards.iso.org/iso/19115/-3/cat/1.0',
            'gfc': 'http://standards.iso.org/iso/19110/gfc/1.1',
            'cit': 'http://standards.iso.org/iso/19115/-3/cit/2.0',
            'gcx': 'http://standards.iso.org/iso/19115/-3/gcx/1.0',
            'gex': 'http://standards.iso.org/iso/19115/-3/gex/1.0',
            'lan': 'http://standards.iso.org/iso/19115/-3/lan/1.0',
            'srv': 'http://standards.iso.org/iso/19115/-3/srv/2.1',
            'mas': 'http://standards.iso.org/iso/19115/-3/mas/1.0',
            'mcc': 'http://standards.iso.org/iso/19115/-3/mcc/1.0',
            'mco': 'http://standards.iso.org/iso/19115/-3/mco/1.0',
            'mda': 'http://standards.iso.org/iso/19115/-3/mda/1.0',
            'mds': 'http://standards.iso.org/iso/19115/-3/mds/2.0',
            'mdt': 'http://standards.iso.org/iso/19115/-3/mdt/2.0',
            'mex': 'http://standards.iso.org/iso/19115/-3/mex/1.0',
            'mmi': 'http://standards.iso.org/iso/19115/-3/mmi/1.0',
            'mpc': 'http://standards.iso.org/iso/19115/-3/mpc/1.0',
            'mrc': 'http://standards.iso.org/iso/19115/-3/mrc/2.0',
            'mrd': 'http://standards.iso.org/iso/19115/-3/mrd/1.0',
            'mri': 'http://standards.iso.org/iso/19115/-3/mri/1.0',
            'mrl': 'http://standards.iso.org/iso/19115/-3/mrl/2.0',
            'mrs': 'http://standards.iso.org/iso/19115/-3/mrs/1.0',
            'msr': 'http://standards.iso.org/iso/19115/-3/msr/2.0',
            'mdq': 'http://standards.iso.org/iso/19157/-2/mdq/1.0',
            'mac': 'http://standards.iso.org/iso/19115/-3/mac/2.0',
            'gco': 'http://standards.iso.org/iso/19115/-3/gco/1.0',
            'gml': 'http://www.opengis.net/gml/3.2',
            'xlink': 'http://www.w3.org/1999/xlink',
            'gmd': 'http://www.isotc211.org/2005/gmd'
        }