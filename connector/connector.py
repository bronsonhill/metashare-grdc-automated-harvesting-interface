import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from abc import ABC, abstractmethod
import json

class ConnectorInterface(ABC):
    @abstractmethod
    def can_connect(self):
        pass

    @abstractmethod
    def search_records(self, query):
        pass

    @abstractmethod
    def get_record(self, uuid):
        pass


from config import ConfigLoader, SourceConfig


class GeoNetworkConnector(ConnectorInterface):
    def __init__(self):
        self.source_config = ConfigLoader().source_config
        self.url = self.source_config.url
        self.search_endpoint = self.source_config.search_endpoint
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        self.hit_count = 0
        self.filtered_count = 0

    def can_connect(self):
        """
        Test connection to the GeoNetwork API using the site endpoint.
        """
        try:
            url = self.url.rstrip('/') + '/' + self.source_config.test_endpoint.lstrip('/')
            response = self.session.get(url)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to GeoNetwork: {e}")
            return False

    def search_records(self, query):
        self.session.headers.update({
            "Accept": "application/xml"
        })

        json_records = self._search_records_json(query)
        uuids = self._get_uuids_from_records(json_records)
        xml_records = self._get_records_xml(uuids)
        return xml_records
        
    def get_record(self, uuid):
        # test record uuid e1331a40-cd41-4506-acfe-dc4bdeee6275
        try:
            # set accept header to application/xml
            self.session.headers.update({
                "Accept": "application/xml"
            })
            url = self.url.rstrip('/') + '/' + self.source_config.get_record_endpoint.lstrip('/') + '/' + uuid
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error getting record {uuid}: {e}")

    def construct_query(self, since):
        # Initialize with a basic bool query structure that matches all documents
        query_body: Dict[str, Any] = {
            "query": {
                "bool": {
                    "must": [{"match_all": {}}],
                    "filter": []
                }
            },
            "size": self.source_config.maxRecords,
        }

        # Add date range filter if 'since' is provided
        if since:
            # Format date string
            date_str = since.isoformat().replace("+00:00", "Z") if since.tzinfo == timezone.utc else since.isoformat()
            
            date_should_clauses = []
            
            # Add changeDate range
            date_should_clauses.append({
                "range": {
                    "changeDate": {
                        "gt": date_str
                    }
                }
            })
            
            # Add createDate range
            date_should_clauses.append({
                "range": {
                    "createDate": {
                        "gt": date_str
                    }
                }
            })
            
            # Add the date filter with minimum_should_match
            query_body["query"]["bool"]["filter"].append({
                "bool": {
                    "should": date_should_clauses,
                    "minimum_should_match": 1
                }
            })
        
        # filter contact for resource email for containing grdc; must specify which role they may have
        # query_body["query"]["bool"]["filter"].append(
        #     {
        #         "wildcard": {
        #             "ownerForResource.email": "*grdc*"
        #         }
        #     }
        # )

        # filter for contract code in purpose element; must specify the format of the contract code ? No 
        # query_body["query"]["bool"]["filter"].append(
        #     {
        #         "wildcard": {
        #             "purpose": "*grdc*"
        #         }
        #     }
        # )

        return query_body

    def _search_records_json(self, query):

        self.session.headers.update({
            "Accept": "application/json"
        })

        try:
            url = self.url.rstrip('/') + '/' + self.search_endpoint.lstrip('/')
            response = self.session.post(url, json=query)
            response.raise_for_status()

            hits = response.json()['hits']['hits']
            self.hit_count = len(hits)

            filtered_hits = self._filter_results(hits)

            return filtered_hits
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error searching for {query}: {e}")

    def _get_records_xml(self, uuids):
        records = []
        for uuid in uuids:
            record = self.get_record(uuid)
            records.append(record)
        return records

    def _get_uuids_from_records(self, json_records):
        uuids = []
        for record in json_records:
            uuids.append(record['_source']['uuid'])
        return uuids

    def _filter_results(self, results):
        keywords = self.source_config.grdc_filter_keywords
        filtered_results = []
        
        for result in results:
            if self._containts_grdc(result, keywords) or self._is_grdc_metadata(result):
                filtered_results.append(result)

        self.filtered_count = len(filtered_results)

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
        # covered by _containts_grdc
        pass

    def _is_grdc_contract_code(self, result):
        pass

    def _is_grdc_owner(self, result):
        # covered by _containts_grdc
        pass


# if __name__ == "__main__":
    # test search
    # config_loader = ConfigLoader("config_dev.toml")
    # source_config = config_loader.source_config
    # connector = GeoNetworkConnector(source_config)