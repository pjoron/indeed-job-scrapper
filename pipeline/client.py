"""Thin PocketBase REST client"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from config import PB_SUPERUSER_EMAIL, PB_SUPERUSER_PASSWORD, PB_URL


class PocketBaseClient:
    def __init__(self, url: str = PB_URL,
                 email: str = PB_SUPERUSER_EMAIL,
                 password: str = PB_SUPERUSER_PASSWORD,
                 timeout: float = 20.0):
        self.url = url.rstrip("/")
        self._client = httpx.Client(timeout=timeout)
        self._token = self._authenticate(email, password)
        self._client.headers["Authorization"] = self._token

    def _authenticate(self, email: str, password: str) -> str:
        r = self._client.post(
            f"{self.url}/api/collections/_superusers/auth-with-password",
            json={"identity": email, "password": password},
        )
        r.raise_for_status()
        return r.json()["token"]

    # CRUD

    def list_all(self, collection: str, filter_: Optional[str] = None,
                 fields: Optional[str] = None) -> list[dict[str, Any]]:
        """Fetch every record of a collection (handles pagination)."""
        items: list[dict] = []
        page = 1
        while True:
            params: dict[str, Any] = {"page": page, "perPage": 500}
            if filter_:
                params["filter"] = filter_
            if fields:
                params["fields"] = fields
            r = self._client.get(
                f"{self.url}/api/collections/{collection}/records", params=params
            )
            r.raise_for_status()
            data = r.json()
            items.extend(data.get("items", []))
            if page >= data.get("totalPages", 1):
                break
            page += 1
        return items

    def create(self, collection: str, data: dict[str, Any]) -> dict[str, Any]:
        r = self._client.post(
            f"{self.url}/api/collections/{collection}/records", json=data
        )
        r.raise_for_status()
        return r.json()

    def update(self, collection: str, record_id: str,
               data: dict[str, Any]) -> dict[str, Any]:
        r = self._client.patch(
            f"{self.url}/api/collections/{collection}/records/{record_id}", json=data
        )
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PocketBaseClient":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
