"""Wrappers da OpenAI: embeddings e chat (com e sem streaming)."""

from __future__ import annotations

import os
from collections.abc import Iterator

from openai import OpenAI

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY ausente. Confira o .env.")
        _client = OpenAI(api_key=api_key)
    return _client


def embed(text: str) -> list[float]:
    """Gera embedding de uma string."""
    model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    resp = client().embeddings.create(model=model, input=text[:8000])
    return resp.data[0].embedding


def chat_json(messages: list[dict], temperature: float = 0.3) -> dict:
    """Chat completion forcando JSON. Retorna o objeto parsado."""
    import json

    model = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    resp = client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def chat_stream(messages: list[dict], temperature: float = 0.5) -> Iterator[str]:
    """Streaming de tokens — usado pelo endpoint de chat SSE."""
    model = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    stream = client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def tts_stream(text: str, voice: str = "alloy") -> Iterator[bytes]:
    """Streaming de MP3 via OpenAI TTS. Vozes: alloy, echo, fable, onyx, nova, shimmer."""
    model = os.environ.get("OPENAI_TTS_MODEL", "tts-1")
    # API streaming nova - chega em chunks conforme o servidor gera
    with client().audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=text[:4000],
        response_format="mp3",
    ) as response:
        for chunk in response.iter_bytes(chunk_size=8192):
            yield chunk
