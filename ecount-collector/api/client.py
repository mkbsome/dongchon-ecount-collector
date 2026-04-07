# -*- coding: utf-8 -*-
"""
REST API 클라이언트 (서버 업로드용)
"""

import requests
from typing import Dict, List, Any
import logging

import config

logger = logging.getLogger(__name__)


class APIClient:
    """REST API 클라이언트"""

    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or config.API_BASE_URL
        self.api_key = api_key or config.API_KEY
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })

    def upload_sales(self, records: List[Dict[str, Any]]) -> Dict:
        """판매 데이터 업로드"""
        return self._post("/api/sales/bulk", {"records": records})

    def upload_purchase(self, records: List[Dict[str, Any]]) -> Dict:
        """구매 데이터 업로드"""
        return self._post("/api/purchase/bulk", {"records": records})

    def upload_production(self, records: List[Dict[str, Any]]) -> Dict:
        """생산 데이터 업로드"""
        return self._post("/api/production/bulk", {"records": records})

    def get_last_sync_date(self, data_type: str) -> str:
        """마지막 동기화 날짜 조회"""
        try:
            response = self._get(f"/api/sync/last-date/{data_type}")
            return response.get("last_date")
        except Exception as e:
            logger.warning(f"Failed to get last sync date: {e}")
            return None

    def get_missing_dates(self, data_type: str, start_date: str, end_date: str) -> List[str]:
        """누락된 날짜 목록 조회"""
        try:
            response = self._get(f"/api/sync/missing-dates/{data_type}", params={
                "start_date": start_date,
                "end_date": end_date
            })
            return response.get("missing_dates", [])
        except Exception as e:
            logger.warning(f"Failed to get missing dates: {e}")
            return []

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """GET 요청"""
        if not self.base_url:
            logger.warning("API base URL not configured")
            return {}

        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, data: Dict) -> Dict:
        """POST 요청"""
        if not self.base_url:
            logger.warning("API base URL not configured, skipping upload")
            return {"status": "skipped", "reason": "API not configured"}

        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def upload(self, data_type: str, records: List[Dict[str, Any]]) -> Dict:
        """데이터 유형에 따라 업로드"""
        uploaders = {
            "sales": self.upload_sales,
            "purchase": self.upload_purchase,
            "production": self.upload_production
        }

        uploader = uploaders.get(data_type)
        if not uploader:
            raise ValueError(f"Unknown data type: {data_type}")

        return uploader(records)
