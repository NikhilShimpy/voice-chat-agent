import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.asyncio
async def test_websocket_connection():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        # Test connection establishment
        assert "type" in data