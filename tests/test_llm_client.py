import io
import json
import urllib.error

from backend.llm_client import ChatMessage, LLMError, OpenAICompatibleClient
from backend.models import LLMConfig


class FakeResponse:
    def __init__(self, data: dict | str) -> None:
        if isinstance(data, str):
            self.payload = data.encode("utf-8")
        else:
            self.payload = json.dumps(data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return self.payload


def _http_error(code: int, body: dict | str) -> urllib.error.HTTPError:
    payload = json.dumps(body).encode("utf-8") if isinstance(body, dict) else body.encode("utf-8")
    return urllib.error.HTTPError("https://example.test", code, "Bad Request", {}, io.BytesIO(payload))


def test_response_format_400_falls_back_without_json_object(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    request_bodies = []

    def fake_urlopen(request, timeout):  # noqa: ANN001 - mirrors urllib signature.
        request_bodies.append(json.loads(request.data.decode("utf-8")))
        if len(request_bodies) == 1:
            raise _http_error(400, {"error": {"message": "response_format is not supported"}})
        return FakeResponse({"choices": [{"message": {"content": '{"ok": true}'}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    content = OpenAICompatibleClient(LLMConfig(model="fake")).chat([ChatMessage("user", "test")])

    assert content == '{"ok": true}'
    assert "response_format" in request_bodies[0]
    assert "response_format" not in request_bodies[1]


def test_http_error_body_is_summarized(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_urlopen(_request, timeout):  # noqa: ANN001 - mirrors urllib signature.
        raise _http_error(401, {"error": {"message": "bad key", "type": "auth_error"}})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    try:
        OpenAICompatibleClient(LLMConfig(model="fake", max_retries=0)).chat([ChatMessage("user", "test")])
    except LLMError as exc:
        assert "bad key (auth_error)" in str(exc)
    else:
        raise AssertionError("expected LLMError")


def test_non_json_response_reports_clear_error(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("urllib.request.urlopen", lambda _request, timeout: FakeResponse("not json"))

    try:
        OpenAICompatibleClient(LLMConfig(model="fake", max_retries=0)).chat([ChatMessage("user", "test")])
    except LLMError as exc:
        assert "不是合法 JSON" in str(exc)
    else:
        raise AssertionError("expected LLMError")


def test_extra_headers_are_sent(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    seen_headers = {}

    def fake_urlopen(request, timeout):  # noqa: ANN001 - mirrors urllib signature.
        seen_headers["x-test"] = request.get_header("X-test")
        return FakeResponse({"choices": [{"message": {"content": '{"ok": true}'}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    config = LLMConfig(model="fake", extra_headers={"X-Test": "tenant-a"})

    OpenAICompatibleClient(config).chat([ChatMessage("user", "test")])

    assert seen_headers["x-test"] == "tenant-a"
