def test_websocket_presence_broadcasts_disconnect_updates(client):
    join_one = {
        "type": "presence.join",
        "board_id": "board-1",
        "user": {"guest_id": "g1", "display_name": "Guest 1"},
    }
    join_two = {
        "type": "presence.join",
        "board_id": "board-1",
        "user": {"guest_id": "g2", "display_name": "Guest 2"},
    }

    with client.websocket_connect("/ws") as first:
        first.send_json(join_one)
        own_snapshot = first.receive_json()
        assert own_snapshot["type"] == "presence.snapshot"
        assert len(own_snapshot["payload"]["users"]) == 1

        with client.websocket_connect("/ws") as second:
            second.send_json(join_two)
            second_snapshot = second.receive_json()
            assert second_snapshot["type"] == "presence.snapshot"
            joined_snapshot = first.receive_json()
            assert joined_snapshot["type"] == "presence.snapshot"
            assert len(joined_snapshot["payload"]["users"]) == 2

        after_disconnect = first.receive_json()
        assert after_disconnect["type"] == "presence.updated"
        assert len(after_disconnect["payload"]["users"]) == 1
        assert after_disconnect["payload"]["users"][0]["guest_id"] == "g1"


def test_websocket_alias_endpoint_accepts_presence(client):
    with client.websocket_connect("/api/ws") as socket:
        socket.send_json(
            {
                "type": "presence.join",
                "board_id": "board-alias",
                "user": {"guest_id": "g1", "display_name": "Alias Guest"},
            }
        )
        snapshot = socket.receive_json()
        assert snapshot["type"] == "presence.snapshot"
        assert snapshot["payload"]["board_id"] == "board-alias"


def test_websocket_reports_missing_board_id(client):
    with client.websocket_connect("/ws") as socket:
        socket.send_json({"type": "presence.join", "user": {"guest_id": "g1"}})
        error = socket.receive_json()
        assert error["type"] == "system.error"
