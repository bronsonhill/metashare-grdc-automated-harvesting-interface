import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from abc import ABC, abstractmethod

class ConnectorInterface(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def search(self, query):
        pass


from config_loader import ConfigLoader, SourceConfig


class GeoNetworkConnector(ConnectorInterface):
    def __init__(self, source_config: SourceConfig):
        self.source_config = source_config
        self.url = source_config.url
        self.search_endpoint = source_config.search_endpoint
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def connect(self):
        pass

    def search(self, query):
        try:
            url = self.url.rstrip('/') + '/' + self.search_endpoint.lstrip('/')
            response = self.session.post(url, json=query)
            response.raise_for_status()
            hits = response.json()['hits']['hits']
            print(f"Number of hits: {len(hits)}")
            return self._filter_results(hits)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error searching for {query}: {e}")

    def construct_query(self, since):

        query_body: Dict[str, Any] = {
            "query": {
                "match_all": {}
            },
            "size": self.source_config.maxRecords,
        }

        # Add date range filter if 'since' is provided
        if since:
            # Assuming 'changeDate' is the field for modification time in GeoNetwork/ES
            # Adjust field name if necessary based on specific GeoNetwork schema
            # Ensure we use a format compatible with the server, isoformat() usually works well.
            # If since is timezone aware, it includes offset.
            query_body["query"] = {
                "bool": {
                    "must": [{"match_all": {}}],
                    "filter": [
                        {
                            "bool": {
                                "should": [
                                    {
                                        "range": {
                                            "changeDate": {
                                                "gt": since.isoformat().replace("+00:00", "Z") if since.tzinfo == timezone.utc else since.isoformat()
                                            }
                                        }
                                    },
                                    {
                                        "range": {
                                            "createDate": {
                                                "gt": since.isoformat().replace("+00:00", "Z") if since.tzinfo == timezone.utc else since.isoformat()
                                            }
                                        }
                                    }
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    ]
                }
            }
        
        return query_body

    def _filter_results(self, results):
        keywords = self.source_config.grdc_filter_keywords
        filtered_results = []
        
        for result in results:
            if self._containts_grdc(result, keywords) or self._is_grdc_metadata(result):
                filtered_results.append(result)
        print("Filtered hits: ", len(filtered_results))
        return filtered_results

    def _containts_grdc(self, result, keywords):
        """Check if any field in the result contains any of the keywords."""
        for value in result.values():
            value_str = str(value)
            for keyword in keywords:
                if keyword in value_str:
                    return True
        return False

    def _is_grdc_metadata(self, result):
        return self._is_grdc_contact(result) or self._is_grdc_contract_code(result) or self._is_grdc_owner(result)

    def _is_grdc_contact(self, result):
        return "grdc" in result.get("contact", "")

    def _is_grdc_contract_code(self, result):
        pass

    def _is_grdc_owner(self, result):
        pass


if __name__ == "__main__":
    config_loader = ConfigLoader()
    source_config = config_loader.get_source_config()
    connector = GeoNetworkConnector(source_config)
    results = connector.search(connector.construct_query(datetime.now(timezone.utc) - timedelta(days=14))) 
    filtered_results = connector.filter_results(results)