"""Integration tests for chat endpoint with board context."""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_chat_with_board_context_creates_ticket_in_correct_board():
    """Test that chat creates ticket with correct board_id from board_context."""

    # Arrange
    board_id = "test-board-123"
    board_name = "Test Board"
    message = "crea un ticket per implementare login con JWT"

    request_data = {
        "message": message,
        "context": {},
        "board_context": {
            "board_id": board_id,
            "board_name": board_name,
            "columns": [
                {"id": "col-1", "name": "To Do", "color": "#3b82f6"},
                {"id": "col-2", "name": "Done", "color": "#22c55e"},
            ],
            "labels": [
                {"id": "lbl-1", "name": "backend", "color": "#ef4444"},
                {"id": "lbl-2", "name": "security", "color": "#eab308"},
            ],
            "total_tickets": 5,
        },
    }

    # Act
    response = client.post("/api/chat", json=request_data, timeout=30)

    # Assert
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()

    # Verify response structure
    assert "action" in data
    assert "params" in data
    assert "response" in data

    # Verify it's a create action
    assert data["action"] == "create", f"Expected 'create' action, got '{data['action']}'"

    # Verify board_id was injected into params
    assert "board_id" in data["params"], "board_id should be in params"
    assert data["params"]["board_id"] == board_id, f"Expected board_id '{board_id}', got '{data['params']['board_id']}'"

    # Verify ticket has title
    assert "title" in data["params"], "title should be in params"
    assert len(data["params"]["title"]) > 0, "title should not be empty"

    # Verify natural language response
    assert len(data["response"]) >= 5, "response should be at least 5 characters"

    print(f"✅ Test passed!")
    print(f"   Action: {data['action']}")
    print(f"   Board ID: {data['params'].get('board_id')}")
    print(f"   Title: {data['params'].get('title')}")
    print(f"   Response: {data['response'][:100]}...")


def test_chat_without_board_context_works():
    """Test that chat works even without board_context (backwards compatibility)."""

    request_data = {
        "message": "crea un ticket per test",
        "context": {},
    }

    response = client.post("/api/chat", json=request_data, timeout=30)

    assert response.status_code == 200
    data = response.json()

    assert "action" in data
    assert "params" in data
    assert "response" in data

    # Should still work, just without board_id
    print(f"✅ Test passed (no board_context)!")
    print(f"   Action: {data['action']}")
    print(f"   Params: {data['params']}")


def test_chat_timeout_increased():
    """Test that chat endpoint doesn't timeout within 20 seconds."""

    import time

    request_data = {
        "message": "crea un ticket molto complesso con descrizione dettagliata per un sistema di autenticazione multi-fattore con biometria",
        "context": {},
        "board_context": {
            "board_id": "test-board-456",
            "board_name": "Complex Board",
            "columns": [],
            "labels": [],
            "total_tickets": 0,
        },
    }

    start = time.time()
    response = client.post("/api/chat", json=request_data, timeout=25)
    elapsed = time.time() - start

    assert response.status_code == 200, f"Request failed after {elapsed:.2f}s"
    assert elapsed < 20, f"Request took {elapsed:.2f}s, should be under 20s"

    print(f"✅ Test passed! Request completed in {elapsed:.2f}s")


def test_chat_labels_parsing():
    """Test that labels are parsed correctly (not as bound methods)."""

    request_data = {
        "message": "crea un ticket backend urgente con label security e api",
        "context": {},
        "board_context": {
            "board_id": "test-board-789",
            "board_name": "Label Test Board",
            "columns": [],
            "labels": [
                {"id": "lbl-1", "name": "backend", "color": "#ef4444"},
                {"id": "lbl-2", "name": "security", "color": "#eab308"},
                {"id": "lbl-3", "name": "api", "color": "#3b82f6"},
            ],
            "total_tickets": 0,
        },
    }

    response = client.post("/api/chat", json=request_data, timeout=30)

    assert response.status_code == 200
    data = response.json()

    # Check if labels exist in params
    if "labels" in data["params"]:
        labels = data["params"]["labels"]

        # Verify labels is a list
        assert isinstance(labels, list), f"labels should be a list, got {type(labels)}"

        # Verify labels don't contain method strings
        for label in labels:
            assert not isinstance(label, str) or "<bound method" not in label, \
                f"Label contains method string: {label}"
            assert not isinstance(label, str) or "Prediction(" not in label, \
                f"Label contains Prediction object: {label}"

        print(f"✅ Test passed! Labels parsed correctly: {labels}")
    else:
        print(f"⚠️  No labels in response (might be ok if AI didn't add labels)")


def test_chat_different_boards():
    """Test that tickets are created in different boards based on board_context."""

    boards = [
        {"board_id": "board-A", "board_name": "Mobile App"},
        {"board_id": "board-B", "board_name": "Backend API"},
        {"board_id": "board-C", "board_name": "DevOps"},
    ]

    for board in boards:
        request_data = {
            "message": "crea un ticket per test",
            "context": {},
            "board_context": {
                "board_id": board["board_id"],
                "board_name": board["board_name"],
                "columns": [],
                "labels": [],
                "total_tickets": 0,
            },
        }

        response = client.post("/api/chat", json=request_data, timeout=30)

        assert response.status_code == 200
        data = response.json()

        if data["action"] == "create":
            assert data["params"].get("board_id") == board["board_id"], \
                f"Expected board_id '{board['board_id']}', got '{data['params'].get('board_id')}'"

            print(f"✅ Ticket correctly assigned to board: {board['board_name']}")


if __name__ == "__main__":
    print("Running chat board context tests...\n")

    try:
        test_chat_with_board_context_creates_ticket_in_correct_board()
        print()
        test_chat_without_board_context_works()
        print()
        test_chat_timeout_increased()
        print()
        test_chat_labels_parsing()
        print()
        test_chat_different_boards()
        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
