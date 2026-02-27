"""Tests for WebSocket connection manager."""


from app.core.websocket import ConnectionManager


class FakeWebSocket:
    """Minimal fake WebSocket for unit testing."""

    def __init__(self) -> None:
        self.accepted = False
        self.sent_messages: list[str] = []
        self.closed = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_text(self, text: str) -> None:
        if self.closed:
            raise RuntimeError("WebSocket closed")
        self.sent_messages.append(text)


class TestConnectionManager:
    """Tests for the WebSocket ConnectionManager."""

    async def test_websocket_connect(self):
        mgr = ConnectionManager()
        ws = FakeWebSocket()
        await mgr.connect(ws)
        assert ws.accepted
        assert mgr.active_count == 1

    async def test_websocket_disconnect_cleanup(self):
        mgr = ConnectionManager()
        ws = FakeWebSocket()
        await mgr.connect(ws)
        mgr.disconnect(ws)
        assert mgr.active_count == 0

    async def test_websocket_receives_broadcast(self):
        mgr = ConnectionManager()
        ws = FakeWebSocket()
        await mgr.connect(ws)
        await mgr.broadcast({"step": "filling", "status": "in_progress"})
        assert len(ws.sent_messages) == 1
        assert "filling" in ws.sent_messages[0]

    async def test_multiple_clients_receive_broadcast(self):
        mgr = ConnectionManager()
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        await mgr.connect(ws1)
        await mgr.connect(ws2)
        await mgr.broadcast({"step": "submit"})
        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 1

    async def test_broadcast_removes_disconnected(self):
        mgr = ConnectionManager()
        ws_good = FakeWebSocket()
        ws_bad = FakeWebSocket()
        ws_bad.closed = True  # Simulate disconnected
        await mgr.connect(ws_good)
        await mgr.connect(ws_bad)
        assert mgr.active_count == 2

        await mgr.broadcast({"step": "test"})
        # Bad socket should be removed
        assert mgr.active_count == 1
        assert len(ws_good.sent_messages) == 1

    async def test_send_personal(self):
        mgr = ConnectionManager()
        ws = FakeWebSocket()
        await mgr.connect(ws)
        await mgr.send_personal(ws, {"private": True})
        assert len(ws.sent_messages) == 1
        assert "private" in ws.sent_messages[0]
