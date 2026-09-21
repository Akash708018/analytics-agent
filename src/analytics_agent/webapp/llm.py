"""Model providers for the Track B agent loop: Gemini, with Groq as failover (guide Phase 14 item 3).

No SDKs. Each provider is one JSON POST over urllib, translated to and from one small internal
shape: a `Reply` holding text and/or tool calls. A `Session` keeps the provider's own message list,
so each wire format is spoken exactly -- Gemini's model content is echoed back verbatim, whatever
parts it holds, rather than rebuilt from what this module understood of it.

Keys come from the environment or a gitignored .env at the repository root (`load_env`), are sent
in headers, and never appear in an error message or a log line.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from analytics_agent.config import PROJECT_ROOT

TIMEOUT_S = 60
#: Sent on every request. Python's default "Python-urllib/3.x" is refused by Groq's edge with
#: HTTP 403 "error code: 1010" (Cloudflare's banned-signature code); measured: default 403, this 200.
USER_AGENT = "analytics-agent/0.1 (+https://github.com/Akash708018/analytics-agent)"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"
GROQ_URL = "https://api.groq.com/openai/v1"

#: Schema keys a function declaration keeps. Gemini accepts an OpenAPI subset and rejects the rest
#: (measured on the engine's own tools: anyOf x105, default x122, additionalProperties x36).
_KEEP = {"type", "description", "properties", "required", "items", "enum", "format", "nullable"}


class ProviderError(Exception):
    """A provider call failed. `retryable` -- rate limit, server error, timeout -- lets the loop
    fail over; anything else (a bad key, a rejected request) is reported, not retried."""

    def __init__(self, provider: str, message: str, retryable: bool) -> None:
        super().__init__(f"{provider}: {message}")
        self.provider = provider
        self.retryable = retryable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict  # already converted by convert_schema


@dataclass(frozen=True)
class Call:
    id: str
    name: str
    args: dict


@dataclass
class Reply:
    text: str = ""
    calls: list[Call] = field(default_factory=list)


class Session(Protocol):
    def step(self) -> Reply: ...
    def add_results(self, results: list[tuple[Call, str]]) -> None: ...


class Provider(Protocol):
    name: str

    def available(self) -> bool: ...
    def start(self, system: str, history: list[dict], message: str,
              tools: list[ToolSpec]) -> Session: ...


# --- environment -------------------------------------------------------------------------------

def load_env(path: Path | None = None) -> list[str]:
    """Read KEY=VALUE lines from the repository's .env into os.environ, never overwriting what is
    already set. Returns the NAMES loaded, never the values."""
    path = path or PROJECT_ROOT / ".env"
    loaded: list[str] = []
    if not path.is_file():
        return loaded
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded


# --- schemas -----------------------------------------------------------------------------------

def convert_schema(schema: Any, *, drop: frozenset[str] = frozenset({"workspace_id"})) -> Any:
    """A FastMCP JSON schema as a function declaration's parameters.

    `anyOf: [X, {type: null}]` becomes X with nullable, keys outside the OpenAPI subset go, and
    the properties named in `drop` are removed -- the model never chooses a workspace.
    """
    if isinstance(schema, list):
        return [convert_schema(s, drop=drop) for s in schema]
    if not isinstance(schema, dict):
        return schema
    if "anyOf" in schema:
        branches = [b for b in schema["anyOf"] if b.get("type") != "null"]
        merged = dict(branches[0]) if len(branches) == 1 else {"type": "string"}
        if len(branches) < len(schema["anyOf"]):
            merged["nullable"] = True
        if "description" in schema:
            merged.setdefault("description", schema["description"])
        return convert_schema(merged, drop=drop)
    out: dict = {}
    for key, value in schema.items():
        if key not in _KEEP:
            continue
        if key == "properties":
            out[key] = {k: convert_schema(v, drop=drop) for k, v in value.items() if k not in drop}
        elif key == "required":
            out[key] = [k for k in value if k not in drop]
        else:
            out[key] = convert_schema(value, drop=drop)
    if out.get("type") == "object" and "properties" not in out:
        out["properties"] = {}
    if not out.get("required"):
        out.pop("required", None)
    return out


def to_json_schema(schema: Any) -> Any:
    """The converted (OpenAPI-subset) schema in standard JSON Schema, for OpenAI-compatible
    providers: `nullable: true` becomes a type list with "null".

    Groq validates a model's tool call against the schema it was given and does not know the
    OpenAPI keyword, so gpt-oss's `"question": null` for an optional field was refused with
    "expected string, but got null" (measured live, P14-D27). Gemini keeps `nullable`.
    """
    if isinstance(schema, list):
        return [to_json_schema(s) for s in schema]
    if not isinstance(schema, dict):
        return schema
    out = {k: (to_json_schema(v) if k != "properties"
               else {name: to_json_schema(sub) for name, sub in v.items()})
           for k, v in schema.items() if k != "nullable"}
    if schema.get("nullable") and isinstance(out.get("type"), str):
        out["type"] = [out["type"], "null"]
    return out


# --- HTTP --------------------------------------------------------------------------------------

#: Waiting on a busy provider. Measured on the free tiers, 22/09/2026: Gemini answered 503 "high
#: demand", and Groq 429 on tokens-per-minute with "Please try again in 3.9675s" -- each request
#: carries ~5,000 tokens of tool manuals against Groq's 8,000 a minute. A wait the provider asks
#: for is honoured up to MAX_WAIT_S; a longer one (a spent daily quota) fails over instead of
#: stalling the person (P14-D26).
ATTEMPTS = 3
#: One rate-limit window. Gemini's free tier allows 5 requests a minute on gemini-3.8-flash and
#: asked for "retry in 40.26s"; a 20 s cap failed over instead (measured, P14-D26). A per-minute
#: limit always clears within 60 s; a spent daily quota asks for hours and still fails over.
MAX_WAIT_S = 60.0
BACKOFF_S = (2.0, 5.0)
_WAIT_HINT = re.compile(r"(?:try again in|retry in)\s+([0-9.]+)\s*(ms|s)\b", re.I)
_RETRY_DELAY = re.compile(r'"retryDelay"\s*:\s*"([0-9.]+)s"')
_sleep = time.sleep  # a test replaces it


def _wait_for(exc: urllib.error.HTTPError, detail: str, attempt: int) -> float:
    """Seconds the provider asked us to wait: Retry-After, Groq's "try again in Xs", Gemini's
    retryDelay -- else a short backoff."""
    header = exc.headers.get("Retry-After") if exc.headers else None
    if header and header.replace(".", "", 1).isdigit():
        return float(header)
    m = _WAIT_HINT.search(detail)
    if m:
        return float(m.group(1)) / (1000 if m.group(2).lower() == "ms" else 1)
    m = _RETRY_DELAY.search(detail)
    if m:
        return float(m.group(1))
    return BACKOFF_S[min(attempt, len(BACKOFF_S) - 1)]


def _request(provider: str, url: str, headers: dict, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    for attempt in range(ATTEMPTS):
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json", "User-Agent": USER_AGENT, **headers})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            busy = exc.code in (429, 500, 502, 503, 504)
            if busy and attempt + 1 < ATTEMPTS:
                wait = _wait_for(exc, detail, attempt)
                if wait <= MAX_WAIT_S:
                    _sleep(wait + 0.25)
                    continue
            raise ProviderError(provider, f"HTTP {exc.code}: {detail}",
                                retryable=exc.code == 429 or exc.code >= 500) from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt + 1 < ATTEMPTS:
                _sleep(BACKOFF_S[min(attempt, len(BACKOFF_S) - 1)])
                continue
            raise ProviderError(provider, f"no response ({type(exc).__name__})", True) from None
    raise AssertionError("unreachable")


# --- Gemini ------------------------------------------------------------------------------------

def _declaration(t: ToolSpec) -> dict:
    """A Gemini function declaration. A tool left with no parameters once workspace_id is gone
    (list_datasets, get_workflow_state) omits `parameters`: an OBJECT with empty properties is
    one of the shapes Gemini rejects."""
    out = {"name": t.name, "description": t.description}
    if t.parameters.get("properties"):
        out["parameters"] = t.parameters
    return out


class GeminiSession:
    def __init__(self, provider: "Gemini", system: str, history: list[dict], message: str,
                 tools: list[ToolSpec]) -> None:
        self._p = provider
        self._body: dict = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "model" if m["role"] == "assistant" else "user",
                          "parts": [{"text": m["content"]}]}
                         for m in history if m.get("content")]
            + [{"role": "user", "parts": [{"text": message}]}],
            "tools": [{"functionDeclarations": [_declaration(t) for t in tools]}],
            "toolConfig": {"functionCallingConfig": {"mode": "AUTO"}},
        }

    def step(self) -> Reply:
        data = self._p.post(self._body)
        candidates = data.get("candidates") or []
        if not candidates or "content" not in candidates[0]:
            reason = (candidates[0].get("finishReason") if candidates
                      else data.get("promptFeedback", {}).get("blockReason", "no candidate"))
            raise ProviderError("gemini", f"no content returned ({reason})", retryable=False)
        content = candidates[0]["content"]
        self._body["contents"].append(content)  # verbatim: keeps any signature parts
        reply = Reply()
        for i, part in enumerate(content.get("parts", [])):
            if "functionCall" in part:
                fc = part["functionCall"]
                reply.calls.append(Call(fc.get("id") or f"call_{i}", fc["name"],
                                        dict(fc.get("args") or {})))
            elif "text" in part and not part.get("thought"):
                reply.text += part["text"]
        return reply

    def add_results(self, results: list[tuple[Call, str]]) -> None:
        parts = []
        for call, text in results:
            response: dict = {"name": call.name, "response": {"result": text}}
            if not call.id.startswith("call_"):
                response["id"] = call.id
            parts.append({"functionResponse": response})
        self._body["contents"].append({"role": "user", "parts": parts})


#: gemini-<major>[.<minor>]-flash exactly: no lite, image, tts, preview or other variant.
_NUMBERED_FLASH = re.compile(r"^gemini-(\d+)(?:\.(\d+))?-flash$")


def choose_gemini_model(names: list[str]) -> str:
    """Google's own alias for the current Flash model if it is offered, else the highest-NUMBERED
    plain flash model.

    The first version sorted names as strings, took the last, and got "gemini-omni-1.1-flash" --
    "omni" sorts after "3.8" -- whose free tier returned 429 on the first request. Measured on a
    free key, 22/09/2026: gemini-flash-latest 200 (serving gemini-3.8-flash); gemini-2.5-flash 404
    "no longer available to new users" (P14-D25).
    """
    if "gemini-flash-latest" in names:
        return "gemini-flash-latest"
    numbered = [(int(m.group(1)), int(m.group(2) or 0), n)
                for n in names if (m := _NUMBERED_FLASH.match(n))]
    if numbered:
        return max(numbered)[2]
    flash = [n for n in names if "flash" in n]
    if flash or names:
        return (flash or names)[0]
    raise ProviderError("gemini", "the model list offers nothing that generates", False)


class Gemini:
    name = "gemini"

    def __init__(self) -> None:
        self._model: str | None = None

    def _key(self) -> str:
        return os.environ.get("GEMINI_API_KEY", "")

    def available(self) -> bool:
        return bool(self._key())

    def model(self) -> str:
        """GEMINI_MODEL, or a stable flash model from the provider's own list -- measured, not
        recalled."""
        if self._model is None:
            self._model = os.environ.get("GEMINI_MODEL") or self._discover()
        return self._model

    def _discover(self) -> str:
        data = _request("gemini", f"{GEMINI_URL}/models?pageSize=1000",
                        {"x-goog-api-key": self._key()})
        names = [m["name"].removeprefix("models/") for m in data.get("models", [])
                 if "generateContent" in m.get("supportedGenerationMethods", [])]
        return choose_gemini_model(names)

    def post(self, body: dict) -> dict:
        return _request("gemini", f"{GEMINI_URL}/models/{self.model()}:generateContent",
                        {"x-goog-api-key": self._key()}, body)

    def start(self, system, history, message, tools) -> GeminiSession:
        return GeminiSession(self, system, history, message, tools)


# --- Groq (OpenAI-compatible) ---------------------------------------------------------------------

class GroqSession:
    def __init__(self, provider: "Groq", system: str, history: list[dict], message: str,
                 tools: list[ToolSpec]) -> None:
        self._p = provider
        self._messages: list[dict] = (
            [{"role": "system", "content": system}]
            + [{"role": m["role"], "content": m["content"]} for m in history if m.get("content")]
            + [{"role": "user", "content": message}])
        self._tools = [{"type": "function", "function": {
            "name": t.name, "description": t.description,
            "parameters": to_json_schema(t.parameters)}} for t in tools]

    def step(self) -> Reply:
        data = self._p.post({"messages": self._messages, "tools": self._tools,
                             "tool_choice": "auto"})
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError):
            raise ProviderError("groq", "no message returned", retryable=False) from None
        self._messages.append({k: v for k, v in message.items()
                               if k in ("role", "content", "tool_calls")})
        reply = Reply(text=message.get("content") or "")
        for tc in message.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            reply.calls.append(Call(tc["id"], tc["function"]["name"], args))
        return reply

    def add_results(self, results: list[tuple[Call, str]]) -> None:
        for call, text in results:
            self._messages.append({"role": "tool", "tool_call_id": call.id, "content": text})


class Groq:
    name = "groq"
    #: Tried in order when GROQ_MODEL is unset; the first the account's model list offers wins.
    PREFERENCE = ("llama-3.3-70b-versatile", "openai/gpt-oss-120b", "openai/gpt-oss-20b",
                  "llama-3.1-8b-instant")

    def __init__(self) -> None:
        self._model: str | None = None

    def _key(self) -> str:
        return os.environ.get("GROQ_API_KEY", "")

    def available(self) -> bool:
        return bool(self._key())

    def model(self) -> str:
        if self._model is None:
            self._model = os.environ.get("GROQ_MODEL") or self._discover()
        return self._model

    def _discover(self) -> str:
        data = _request("groq", f"{GROQ_URL}/models", {"Authorization": f"Bearer {self._key()}"})
        offered = {m.get("id") for m in data.get("data", [])}
        for name in self.PREFERENCE:
            if name in offered:
                return name
        raise ProviderError("groq", f"none of {', '.join(self.PREFERENCE)} is offered; set "
                            "GROQ_MODEL to a tool-calling model", retryable=False)

    def post(self, body: dict) -> dict:
        return _request("groq", f"{GROQ_URL}/chat/completions",
                        {"Authorization": f"Bearer {self._key()}"},
                        {"model": self.model(), **body})

    def start(self, system, history, message, tools) -> GroqSession:
        return GroqSession(self, system, history, message, tools)


PROVIDERS = {"gemini": Gemini, "groq": Groq}
_INSTANCES: dict[str, Provider] = {}  # one each per process, so a model is discovered once


def configured() -> list[Provider]:
    """Providers in ANALYTICS_LLM order (default gemini,groq) that have a key."""
    load_env()
    order = [n.strip() for n in os.environ.get("ANALYTICS_LLM", "gemini,groq").split(",")]
    for n in order:
        if n in PROVIDERS and n not in _INSTANCES:
            _INSTANCES[n] = PROVIDERS[n]()
    return [_INSTANCES[n] for n in order if n in _INSTANCES and _INSTANCES[n].available()]


__all__ = ["Call", "Gemini", "Groq", "Provider", "ProviderError", "Reply", "Session", "ToolSpec",
           "choose_gemini_model", "configured", "convert_schema",
           "load_env", "to_json_schema"]
