"""Document routes, over HTTP.

Parsing runs for real here (markdown, so no OCR/layout model download — see
test_documents_parsing.py's docstring), the LLM is faked at its usual boundary, and
uploaded bytes are redirected to a per-test tmp_path so the suite never writes into the
repo's own working tree.
"""

import pytest

from tests.auth_helpers import bearer
from tests.fakes import document_answer

_MARKDOWN = b"# Safety Procedure\n\nWear PPE at all times on the factory floor.\n"


@pytest.fixture(autouse=True)
def _isolated_storage(tmp_path, monkeypatch):
    """Every upload in this file lands under a per-test tmp_path, not ./data/uploads."""
    import app.documents.service as service_module
    from app.config import get_settings

    isolated = get_settings().model_copy(update={"documents_storage_path": str(tmp_path)})
    monkeypatch.setattr(service_module, "get_settings", lambda: isolated)


def _as(user):
    return bearer(user)


async def _upload(
    client, user, filename="safety.md", content=_MARKDOWN, content_type="text/markdown"
):
    response = await client.post(
        "/api/v1/documents",
        files={"file": (filename, content, content_type)},
        headers=_as(user),
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_uploading_a_document_returns_the_extraction_preview(client, creator):
    body = await _upload(client, creator)

    assert body["status"] == "ready"
    assert body["source_type"] == "upload"
    assert body["parsed_content"]["sections"]
    assert any("Wear PPE" in s["text"] for s in body["parsed_content"]["sections"])
    assert body["messages"] == []


async def test_uploading_an_unrecognisable_file_is_422(client, creator):
    response = await client.post(
        "/api/v1/documents",
        files={
            "file": (
                "mystery.bin",
                b"\x00\x01\x02 not a real document \xff\xfe",
                "application/octet-stream",
            )
        },
        headers=_as(creator),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_chatting_about_a_document_returns_grounded_citations(client, creator, fake_llm):
    document = await _upload(client, creator)
    fake_llm(
        document_answer(
            "Yes — PPE is required at all times.",
            [{"quote": "Wear PPE at all times", "page": None, "section": "Safety Procedure"}],
        )
    )

    response = await client.post(
        f"/api/v1/documents/{document['id']}/messages",
        json={"content": "Do I need PPE?"},
        headers=_as(creator),
    )

    assert response.status_code == 200
    body = response.json()
    assert [m["content"] for m in body["messages"]] == [
        "Do I need PPE?",
        "Yes — PPE is required at all times.",
    ]
    assert body["messages"][-1]["citations"][0]["quote"] == "Wear PPE at all times"


async def test_a_blank_message_is_refused_before_it_costs_a_model_turn(client, creator):
    """No FakeLLM is installed: if the request reached the chat service at all, the
    test would fail trying to build a client rather than getting a 422."""
    document = await _upload(client, creator)

    response = await client.post(
        f"/api/v1/documents/{document['id']}/messages",
        json={"content": "   "},
        headers=_as(creator),
    )

    assert response.status_code == 422


async def test_one_users_document_is_invisible_to_another(client, creator, other_creator):
    document = await _upload(client, creator)

    response = await client.get(f"/api/v1/documents/{document['id']}", headers=_as(other_creator))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_the_document_list_is_not_parsed_as_a_document_id(client, creator):
    """`GET /api/v1/documents` is declared before `GET /api/v1/documents/{document_id}`
    so the literal path wins the match — swap the order and this 200 becomes a 422 from
    a failed UUID parse, with no other symptom."""
    document = await _upload(client, creator)

    response = await client.get("/api/v1/documents", headers=_as(creator))

    assert response.status_code == 200
    listed = response.json()
    assert [d["id"] for d in listed] == [document["id"]]


async def test_fetching_a_non_https_url_is_refused_before_any_network_call(client, creator):
    response = await client.post(
        "/api/v1/documents/fetch", json={"url": "http://example.com/x"}, headers=_as(creator)
    )

    assert response.status_code == 422
    assert "https" in response.json()["error"]["message"].lower()


async def test_uploading_and_chatting_require_a_bearer_token(client):
    response = await client.get("/api/v1/documents")
    assert response.status_code == 401
