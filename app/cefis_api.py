"""Cliente HTTP para as APIs publicas da CEFIS.

A integracao e OPCIONAL: o tutor funciona sem login. Quando o aluno faz login
puxamos nome real + certificados ja conquistados (para evitar recomendar
conteudos repetidos).
"""

from __future__ import annotations

import os
from typing import Any

import httpx

CEFIS_API_BASE = os.environ.get("CEFIS_API_BASE", "https://cefis.com.br").rstrip("/")
CEFIS_API_V3_BASE = os.environ.get(
    "CEFIS_API_V3_BASE", "https://api-v3.cefis.com.br"
).rstrip("/")


class CefisAuthError(Exception):
    """Credenciais invalidas ou key expirada."""


async def login(email: str, password: str) -> dict[str, Any]:
    """POST /api/v1/login - retorna o objeto data inteiro (com key + user)."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{CEFIS_API_BASE}/api/v1/login",
            json={"email": email, "pass": password},
            headers={"Accept": "application/json"},
        )
    if r.status_code == 401:
        raise CefisAuthError("Credenciais invalidas")
    if r.status_code >= 400:
        raise CefisAuthError(f"Erro CEFIS {r.status_code}: {r.text[:200]}")
    body = r.json()
    return body.get("data") or body


async def me(api_key: str) -> dict[str, Any]:
    """GET /api/v1/user/me - dados completos do usuario autenticado."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{CEFIS_API_BASE}/api/v1/user/me",
            headers={"Authorization": api_key, "Accept": "application/json"},
        )
    if r.status_code == 401:
        raise CefisAuthError("Sessao expirou")
    if r.status_code >= 400:
        raise CefisAuthError(f"Erro {r.status_code}")
    body = r.json()
    return body.get("data") or body


async def certificates(api_key: str, count: int = 50) -> list[dict[str, Any]]:
    """GET /performance/certificates - lista de certificados conquistados."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{CEFIS_API_V3_BASE}/performance/certificates",
            params={"count": count, "page": 1},
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        )
    if r.status_code == 401:
        raise CefisAuthError("Sessao expirou")
    if r.status_code >= 400:
        return []
    body = r.json()
    return body.get("data") or []
