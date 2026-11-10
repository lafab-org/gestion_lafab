"""Simulated Paheko API."""

import asyncio
import base64

import httpx

URL = "https://lafab.paheko.cloud"
API_ID = "test-id"
API_TOKEN = "test-token"
ENV = {"PAHEKO_URL": URL, "PAHEKO_API_ID": API_ID, "PAHEKO_API_TOKEN": API_TOKEN}


def basic_auth(api_id: str, token: str) -> str:
    return "Basic " + base64.b64encode(f"{api_id}:{token}".encode()).decode()


class FakePaheko:
    """Accepts the configured credentials, unless told otherwise.

    status: HTTP status answered to accepted credentials.
    error: exception raised instead of answering.
    held: while True, requests wait before being answered.
    """

    def __init__(self) -> None:
        self.status = 200
        self.error: Exception | None = None
        self.held = False
        self.calls = 0

    async def handle(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        while self.held:
            await asyncio.sleep(0.01)
        if self.error is not None:
            raise self.error
        if request.headers.get("authorization") != basic_auth(API_ID, API_TOKEN):
            return httpx.Response(401, json={"error": "unauthorized"})
        return httpx.Response(self.status, json={"count": 1, "results": []})

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handle)
