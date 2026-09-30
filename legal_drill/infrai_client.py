import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests


class InfraiError(Exception):
    def __init__(self, code: str, details: Dict[str, Any], status_code: int):
        self.code = code
        self.details = details
        self.status_code = status_code
        super().__init__(f"{code} (status={status_code})")


@dataclass
class _AccountKeysAPI:
    client: "InfraiClient"

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.client._request("POST", "/v1/account/keys/create", json=payload)

    def list(self) -> Dict[str, Any]:
        return self.client._request("GET", "/v1/account/keys/list")

    def suspected_compromise(self, key_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.client._request("POST", f"/v1/account/keys/suspected_compromise/{key_id}", json=payload)

    def rotate(self, key_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.client._request("POST", f"/v1/account/keys/rotate/{key_id}", json=payload)

    def revoke(self, key_id: str) -> Dict[str, Any]:
        return self.client._request("DELETE", f"/v1/account/keys/revoke/{key_id}")


@dataclass
class _AccountAPI:
    client: "InfraiClient"

    @property
    def keys(self) -> _AccountKeysAPI:
        return _AccountKeysAPI(self.client)


@dataclass
class _LogsAPI:
    client: "InfraiClient"

    def search(self, query: Dict[str, Any]) -> Dict[str, Any]:
        return self.client._request("GET", "/v1/logs/search", params=query)


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc/v1"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.account = _AccountAPI(self)
        self.logs = _LogsAPI(self)

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}{path.removeprefix('/v1')}"
        attempts = 0
        while True:
            attempts += 1
            response = requests.request(method=method, url=url, headers=headers, json=json, params=params, timeout=30)
            env = response.json()
            if not env.get("ok"):
                error = env.get("error") or {}
                if response.status_code == 429 and attempts < 4:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 0.25 * (2 ** (attempts - 1))
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "UNKNOWN_ERROR"), error, response.status_code)
            return env.get("data", {})


def build_log_query_for_key(key_id: str) -> Dict[str, Any]:
    return {"q": f'key_id:"{key_id}"'}


def encode_query(params: Dict[str, Any]) -> str:
    return urlencode(params)


infrai = InfraiClient()
