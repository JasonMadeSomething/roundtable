from fastapi.testclient import TestClient


def test_conversation_document_turn_crud(client: TestClient):
    # Create conversation
    resp = client.post("/api/conversations", json={"name": "Test Conversation"})
    assert resp.status_code == 201
    conv = resp.json()
    conv_id = conv["id"]

    # List conversations
    resp = client.get("/api/conversations")
    assert resp.status_code == 200
    assert any(c["id"] == conv_id for c in resp.json())

    # Get conversation
    resp = client.get(f"/api/conversations/{conv_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Conversation"

    # Upload document
    files = {"file": ("test.txt", b"Hello world")}
    resp = client.post(f"/api/conversations/{conv_id}/documents", files=files)
    assert resp.status_code == 201
    doc = resp.json()
    doc_id = doc["id"]
    assert doc["filename"] == "test.txt"

    # List documents
    resp = client.get(f"/api/conversations/{conv_id}/documents")
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 1 and docs[0]["id"] == doc_id

    # Get document
    resp = client.get(f"/api/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["filename"] == "test.txt"

    # Delete document
    resp = client.delete(f"/api/documents/{doc_id}")
    assert resp.status_code == 204

    # Ensure document deleted
    resp = client.get(f"/api/conversations/{conv_id}/documents")
    assert resp.status_code == 200
    assert resp.json() == []

    # Create turn
    resp = client.post(f"/api/conversations/{conv_id}/turns", json={"query": "Hello"})
    assert resp.status_code == 201
    turn = resp.json()
    turn_id = turn["id"]
    assert turn["turn_number"] == 1

    # List turns
    resp = client.get(f"/api/conversations/{conv_id}/turns")
    assert resp.status_code == 200
    turns = resp.json()
    assert len(turns) == 1 and turns[0]["id"] == turn_id

    # Get turn
    resp = client.get(f"/api/turns/{turn_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == turn_id

    # Delete conversation
    resp = client.delete(f"/api/conversations/{conv_id}")
    assert resp.status_code == 204

    # Ensure conversation deleted
    resp = client.get(f"/api/conversations/{conv_id}")
    assert resp.status_code == 404
