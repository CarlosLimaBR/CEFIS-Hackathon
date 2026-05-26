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


async def t_tts() -> bool:
    step("POST /api/tts (audio MP3 streaming)")
    payload = {"text": "Teste de audio do tutor CEFIS."}
    t0 = time.monotonic()
    total_bytes = 0
    async with httpx.AsyncClient(timeout=60.0) as c:
        try:
            async with c.stream("POST", f"{BASE}/api/tts", json=payload) as r:
                if r.status_code != 200:
                    body = (await r.aread()).decode("utf-8", "replace")
                    fail(f"status={r.status_code} body={body[:300]}")
                    return False
                ctype = r.headers.get("content-type", "")
                if "audio" not in ctype:
                    fail(f"content-type errado: {ctype}")
                    return False
                async for chunk in r.aiter_bytes():
                    total_bytes += len(chunk)
        except httpx.HTTPError as e:
            fail(f"stream falhou: {type(e).__name__}: {e}")
            return False
    dt = time.monotonic() - t0
    if total_bytes < 1000:
        fail(f"audio muito pequeno: {total_bytes} bytes")
        return False
    # MP3 valido comeca com ID3 ou frame sync (FF FB / FF F3 / FF F2)
    ok(f"audio {total_bytes:,} bytes em {dt:.1f}s")
    return True


async def t_quiz(plan: list[dict] | None) -> bool:
    step("POST /api/quiz/{lesson_id} (gera quiz da aula)")
    # acha um lesson_id no plano gerado anteriormente
    lesson_id = None
    if plan:
        for it in plan:
            if it.get("type") == "aula" and it.get("lesson_id"):
                lesson_id = it["lesson_id"]
                break
    if not lesson_id:
        # fallback: busca qualquer aula com transcricao indexada
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.post(
                f"{BASE}/api/onboarding",
                json={
                    "name": "Bot",
                    "areas": [4],
                    "goal": "Quero entender melhoria continua e PDCA",
                    "level": "Iniciante",
                    "minutes": 30,
                },
                timeout=120.0,
            )
            for it in (r.json().get("plan") or []):
                if it.get("type") == "aula" and it.get("lesson_id"):
                    lesson_id = it["lesson_id"]
                    break
    if not lesson_id:
        fail("nenhuma aula com lesson_id disponivel para testar quiz")
        return False
    print(f"     lesson_id={lesson_id}")
    t0 = time.monotonic()
    async with httpx.AsyncClient(timeout=120.0) as c:
        try:
            r = await c.post(f"{BASE}/api/quiz/{lesson_id}")
        except httpx.HTTPError as e:
            fail(f"erro de rede: {e}")
            return False
    dt = time.monotonic() - t0
    if r.status_code != 200:
        fail(f"status={r.status_code} em {dt:.1f}s body={r.text[:500]}")
        return False
    d = r.json()
    questions = d.get("questions") or []
    if len(questions) < 3:
        fail(f"poucas perguntas geradas: {len(questions)}")
        return False
    # valida estrutura
    for i, q in enumerate(questions):
        if not isinstance(q.get("question"), str) or not q["question"].strip():
            fail(f"pergunta {i} sem enunciado: {q}")
            return False
        opts = q.get("options") or []
        if len(opts) < 2:
            fail(f"pergunta {i} com poucas alternativas: {opts}")
            return False
        ci = q.get("correct_index")
        if not isinstance(ci, int) or not 0 <= ci < len(opts):
            fail(f"pergunta {i} correct_index invalido: {ci} (opts={len(opts)})")
            return False
    ok(f"{len(questions)} perguntas em {dt:.1f}s — aula '{d.get('lesson_title')}'")
    q0 = questions[0]
    print(f"     ex.: \"{q0['question'][:80]}\" -> resposta {q0['correct_index']}")
    print(f"          {len(q0['options'])} alternativas, explicacao: {q0.get('explanation','')[:80]}...")
    return True


async def main() -> int:
    print(f"\n=== Teste E2E - Tutor IA CEFIS ===")
    print(f"Base: {BASE}\n")
    results: dict[str, bool] = {}

    results["status"] = await t_status()
    if not results["status"]:
        print("\n!!! /api/status falhou - abortando demais testes")
        return 1

    onb = await t_onboarding()
    results["onboarding"] = bool(onb)
    results["chat"] = await t_chat()
    results["tts"] = await t_tts()
    results["quiz"] = await t_quiz(onb.get("plan") if onb else None)

    # valida que resumos do plano vieram com related_lessons
    if onb:
        step("Validacao: resumos do plano com aulas relacionadas")
        resumos = [it for it in (onb.get("plan") or []) if it.get("type") == "resumo"]
        com_ref = [r for r in resumos if (r.get("related_lessons") or [])]
        if resumos:
            print(f"     {len(com_ref)}/{len(resumos)} resumos com referencia para aula real")
            if com_ref:
                ex = com_ref[0]["related_lessons"][0]
                print(f"     ex.: {ex.get('course_title')} -- {ex.get('lesson_title')}")
                ok(f"resumos tem referencia para aprofundamento")
                results["resumos_com_ref"] = True
            else:
                fail("nenhum resumo veio com related_lessons")
                results["resumos_com_ref"] = False
        else:
            print("     (nenhum resumo neste plano, pulando)")

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
