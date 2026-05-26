"""Smoke test end-to-end dos endpoints do Tutor IA CEFIS.

Bate em /api/status, /api/onboarding e /api/chat (SSE) e reporta cada etapa.
Use enquanto o servidor estiver rodando (iniciar.bat).

    python scripts/test_endpoints.py [BASE_URL]

Default BASE_URL = http://localhost:8000
"""
from __future__ import annotations

import asyncio
import json
import sys
import time

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def ok(msg: str) -> None:
    print(f"  \033[92mOK\033[0m  {msg}")


def fail(msg: str) -> None:
    print(f"  \033[91mFAIL\033[0m  {msg}")


def step(name: str) -> None:
    print(f"\n>>> {name}")


async def t_status() -> bool:
    step("GET /api/status")
    async with httpx.AsyncClient(timeout=10.0) as c:
        try:
            r = await c.get(f"{BASE}/api/status")
        except httpx.ConnectError as e:
            fail(f"servidor nao responde em {BASE} ({e}). Rode iniciar.bat?")
            return False
        if r.status_code != 200:
            fail(f"status={r.status_code} body={r.text[:200]}")
            return False
        d = r.json()
        print(f"     payload: {d}")
        if not d.get("ready"):
            fail(f"index nao pronto: ready={d.get('ready')} embeddings={d.get('embeddings')}")
            return False
        ok(f"ready=True, chunks={d['chunks']}, embeddings={d['embeddings']}")
        return True


async def t_onboarding() -> dict | None:
    step("POST /api/onboarding (gera diagnostico + plano)")
    payload = {
        "name": "TesteAutomatico",
        "areas": [1, 4],
        "goal": "Quero entender PDCA e melhoria continua em 30 minutos",
        "level": "Intermediario",
        "minutes": 30,
    }
    print(f"     payload: {payload}")
    t0 = time.monotonic()
    async with httpx.AsyncClient(timeout=120.0) as c:
        try:
            r = await c.post(f"{BASE}/api/onboarding", json=payload)
        except httpx.HTTPError as e:
            fail(f"erro de rede: {e}")
            return None
    dt = time.monotonic() - t0
    if r.status_code != 200:
        fail(f"status={r.status_code} em {dt:.1f}s body={r.text[:500]}")
        return None
    try:
        d = r.json()
    except Exception as e:
        fail(f"json parse: {e}, body={r.text[:200]}")
        return None
    if not d.get("diagnosis"):
        fail(f"sem diagnostico no payload: {d}")
        return None
    plan = d.get("plan") or []
    if not plan:
        fail(f"plano vazio: {d}")
        return None
    has_aula = any(it.get("type") == "aula" for it in plan)
    has_resumo = any(it.get("type") == "resumo" for it in plan)
    total_min = sum(it.get("duration_minutes") or 0 for it in plan)
    ok(f"diag={len(d['diagnosis'])}c, {len(plan)} itens, total={total_min}min")
    ok(f"tipos: aula={has_aula}, resumo={has_resumo}, tempo_dentro_limite={total_min <= 33}")
    ok(f"latencia: {dt:.1f}s")
    # mostra resumo dos itens
    for i, it in enumerate(plan[:5], 1):
        print(f"     [{i}] {it.get('type')}/{it.get('duration_minutes')}min - {it.get('title', '')[:60]}")
    if len(plan) > 5:
        print(f"     ... mais {len(plan)-5}")
    if not has_aula:
        fail("R1 violada: plano sem nenhuma aula CEFIS real")
        return None
    return d


async def t_chat() -> bool:
    step("POST /api/chat (SSE streaming + RAG)")
    payload = {"message": "Em uma frase: o que e PDCA?", "history": []}
    print(f"     payload: {payload}")
    t0 = time.monotonic()
    eventos: list[str] = []
    tokens: list[str] = []
    sources = None
    first_token_at = None
    error_msg = None
    timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout) as c:
        try:
            async with c.stream("POST", f"{BASE}/api/chat", json=payload) as r:
                if r.status_code != 200:
                    body = (await r.aread()).decode("utf-8", "replace")
                    fail(f"status={r.status_code} body={body[:500]}")
                    return False
                buf = ""
                async for chunk in r.aiter_text():
                    buf += chunk
                    while "\n\n" in buf:
                        block, buf = buf.split("\n\n", 1)
                        ev = {"event": "message", "data": ""}
                        for line in block.split("\n"):
                            if line.startswith("event:"):
                                ev["event"] = line[6:].strip()
                            elif line.startswith("data:"):
                                ev["data"] += line[5:].strip()
                        if not ev["data"]:
                            continue
                        eventos.append(ev["event"])
                        if ev["event"] == "token":
                            try:
                                tok = json.loads(ev["data"]).get("t") or ""
                                if first_token_at is None and tok:
                                    first_token_at = time.monotonic() - t0
                                tokens.append(tok)
                            except json.JSONDecodeError:
                                pass
                        elif ev["event"] == "sources":
                            try:
                                sources = json.loads(ev["data"])
                            except json.JSONDecodeError:
                                pass
                        elif ev["event"] == "error":
                            error_msg = ev["data"]
        except httpx.HTTPError as e:
            fail(f"stream falhou: {type(e).__name__}: {e}")
            return False

    dt = time.monotonic() - t0
    texto = "".join(tokens)
    print(f"     eventos: {eventos[:3]}...{eventos[-3:]} (total {len(eventos)})")
    print(f"     resposta ({len(texto)} chars): {texto[:200]}...")
    if sources is not None:
        print(f"     fontes: {len(sources)} citacoes")
        if sources:
            f0 = sources[0]
            print(f"       ex.: {f0.get('curso')} / {f0.get('aula')} (seg {f0.get('segundo')})")
    if error_msg:
        fail(f"servidor emitiu evento error: {error_msg}")
        return False
    if "sources" not in eventos:
        fail(f"nenhum evento 'sources' recebido. eventos: {eventos}")
        return False
    if "done" not in eventos:
        fail(f"nenhum evento 'done' recebido (stream incompleto). eventos: {eventos[-5:]}")
        return False
    if len(texto) < 5:
        fail(f"resposta muito curta ou vazia ({len(texto)} chars): '{texto}'")
        return False
    ok(f"resposta {len(texto)}c em {dt:.1f}s (primeiro token em {first_token_at:.1f}s)")
    ok(f"fontes: {len(sources or [])} citacoes")
    return True


async def main() -> int:
    print(f"\n=== Teste E2E - Tutor IA CEFIS ===")
    print(f"Base: {BASE}\n")
    results: dict[str, bool] = {}

    results["status"] = await t_status()
    if not results["status"]:
        print("\n!!! /api/status falhou - abortando demais testes")
        return 1

    results["onboarding"] = bool(await t_onboarding())
    results["chat"] = await t_chat()

    print("\n" + "=" * 50)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"{passed}/{total} testes passaram")
    for name, ok_ in results.items():
        mark = "\033[92mOK  \033[0m" if ok_ else "\033[91mFAIL\033[0m"
        print(f"  {mark}  {name}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
