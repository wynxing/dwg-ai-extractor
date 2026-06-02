from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .models import LLMConfig


class LLMError(RuntimeError):
    pass


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str


class OpenAICompatibleClient:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def chat(self, messages: list[ChatMessage]) -> str:
        api_key = self._api_key()
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [{"role": message.role, "content": message.content} for message in messages],
            "temperature": self.config.temperature,
        }
        if self.config.use_json_object:
            payload["response_format"] = {"type": "json_object"}

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        endpoint = self._endpoint()
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            headers.update(self.config.extra_headers)
            request = urllib.request.Request(
                endpoint,
                data=body,
                method="POST",
                headers=headers,
            )
            try:
                with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                    response_text = response.read().decode("utf-8", errors="replace")
                    data = json.loads(response_text)
                return _extract_content(data)
            except urllib.error.HTTPError as exc:
                text = _safe_error_body(exc)
                if exc.code == 400 and self.config.use_json_object and "response_format" in text.lower():
                    fallback = LLMConfig.from_dict(self.config.to_dict())
                    fallback.use_json_object = False
                    return OpenAICompatibleClient(fallback).chat(messages)
                last_error = LLMError(f"模型接口 HTTP {exc.code}: {_format_error_body(text)}")
            except urllib.error.URLError as exc:
                last_error = LLMError(f"模型接口连接失败：{exc.reason}")
            except TimeoutError:
                last_error = LLMError(f"模型接口超时：超过 {self.config.timeout_seconds} 秒")
            except json.JSONDecodeError as exc:
                last_error = LLMError(f"模型接口返回的响应不是合法 JSON：{exc.msg}")
            except (KeyError, IndexError) as exc:
                last_error = LLMError(f"模型接口响应缺少必要字段：{exc}")
            if attempt < self.config.max_retries:
                time.sleep(min(2**attempt, 5))
        raise LLMError(str(last_error or "模型调用失败"))

    def test_connection(self) -> None:
        content = self.chat([ChatMessage("user", 'Return JSON: {"ok": true}')])
        if "ok" not in content:
            raise LLMError("模型连接成功但返回内容不符合预期")

    def _api_key(self) -> str:
        env_name = self.config.api_key_env_var.strip()
        if not env_name:
            raise LLMError("未配置 API Key 环境变量名")
        api_key = os.environ.get(env_name)
        if not api_key:
            raise LLMError(f"环境变量 {env_name} 未设置或为空")
        return api_key

    def _endpoint(self) -> str:
        base_url = self.config.base_url.rstrip("/")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"


def _extract_content(data: dict[str, Any]) -> str:
    choices = data["choices"]
    message = choices[0]["message"]
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    raise LLMError("模型响应中没有可用 content")


def _safe_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", errors="replace")[:1000]
    except Exception:  # noqa: BLE001 - error reporting fallback.
        return exc.reason or "HTTP error"


def _format_error_body(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            error_type = error.get("type")
            if message and error_type:
                return f"{message} ({error_type})"
            if message:
                return str(message)
        if isinstance(error, str):
            return error
        message = data.get("message")
        if isinstance(message, str):
            return message
    return text
