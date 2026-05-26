"""FastAPI app do Tutor IA CEFIS.

Rotas:
    GET  /                  -> serve a SPA estatica
    GET  /api/status        -> estado do indice
    POST /api/onboarding    -> recebe perfil, devolve diagnostico + plano
    POST /api/chat          -> chat com RAG (SSE streaming)
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

from app import cefis_api, db, llm, prompts  # noqa: E402

import logging
import traceback

logger = logging.getLogger("tutor")

SESSION_COOKIE = "cefis_key"


def _openai_error_detail(e: Exception) -> dict:
    """Extrai a mensagem util de um erro OpenAI para devolver ao client."""
    # openai>=1.x: AuthenticationError, RateLimitError, APIConnectionError, etc.
    code = type(e).__name__
    msg = str(e)[:500]
    # tenta extrair body se for httpx error
    body = getattr(e, "body", None)
    if isinstance(body, dict):
        msg = body.get("error", {}).get("message", msg)
    return {"code": code, "message": msg}


def slugify(text: str) -> str:
    """Normaliza o titulo do curso no padrao usado pelas URLs publicas da CEFIS.

    Ex.: "Gestao de Processos" -> "gestao-de-processos"
         "Direito Tributario Avancado" -> "direito-tributario-avancado"
    """
    if not text:
        return "curso"
    # remove acentos
    nfd = unicodedata.normalize("NFD", text)
    no_accent = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    # lowercase + so alfanumerico/hifen
    low = no_accent.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", low)
    return cleaned.strip("-") or "curso"


def course_url(course_id: int, title: str | None) -> str:
    """URL publica de um curso CEFIS: /curso/{slug}/{id}."""
    return f"https://cefis.com.br/curso/{slugify(title or '')}/{course_id}"

APP_DIR = Path(__file__).parent
STATIC_DIR = APP_DIR / "static"

app = FastAPI(title="Tutor IA CEFIS")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class OnboardingRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    areas: list[int] = Field(default_factory=list)
    goal: str = Field(..., min_length=5, max_length=500)
    level: str = Field(..., pattern="^(Iniciante|Intermediario|Avancado)$")
    minutes: int = Field(..., ge=10, le=2400)
    # Filtros opcionais (trilha personalizada / multi-fase)
    course_ids: list[int] | None = Field(default=None)
    exclude_lesson_ids: list[int] = Field(default_factory=list)
    exclude_course_ids: list[int] = Field(default_factory=list)
    phase: int = Field(default=1, ge=1, le=10)
    # Historico do localStorage para o diagnostico ser contextual
    historico_resumo: dict | None = Field(default=None)


class CoursesSearchRequest(BaseModel):
    goal: str = Field(..., min_length=3, max_length=500)
    level: str = Field(default="Iniciante", pattern="^(Iniciante|Intermediario|Avancado)$")
    limit: int = Field(default=12, ge=3, le=30)
    exclude_course_ids: list[int] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    history: list[dict] = Field(default_factory=list, max_length=20)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=120)
    password: str = Field(..., min_length=1, max_length=120)


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    voice: str = Field(default="alloy", pattern="^(alloy|echo|fable|onyx|nova|shimmer)$")


class RoleplayRequest(BaseModel):
    cenario: str = Field(..., min_length=10, max_length=600)
    mensagens: list[dict] = Field(default_factory=list, max_length=30)


class RoleplayFeedbackRequest(BaseModel):
    cenario: str = Field(..., min_length=10, max_length=600)
    mensagens: list[dict] = Field(..., min_length=2, max_length=30)


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
async def status() -> dict:
    return db.index_status()


@app.get("/api/diag")
async def diag() -> dict:
    """Diagnostico rapido: confere .env, conectividade OpenAI, modelos.

    NUNCA expoe a chave inteira — so um prefixo curto.
    """
    out: dict = {"env": {}, "openai": {}, "index": db.index_status()}

    # 1) .env carregado?
    api_key = os.environ.get("OPENAI_API_KEY") or ""
    out["env"]["openai_key_present"] = bool(api_key)
    out["env"]["openai_key_len"] = len(api_key)
    out["env"]["openai_key_prefix"] = api_key[:10] + "..." if api_key else ""
    out["env"]["embedding_model"] = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    out["env"]["chat_model"] = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    out["env"]["data_dir"] = os.environ.get("CEFIS_DATA_DIR", "./Docs/output")
    out["env"]["db_path"] = os.environ.get("CEFIS_DB_PATH", "./data/cefis.db")

    if not api_key:
        out["openai"]["error"] = "OPENAI_API_KEY ausente — .env nao carregado pelo servico"
        return out

    # 2) Embeddings — chamada simples e barata
    try:
        v = llm.embed("ping")
        out["openai"]["embed_ok"] = True
        out["openai"]["embed_dim"] = len(v)
    except Exception as e:
        traceback.print_exc()
        out["openai"]["embed_ok"] = False
        out["openai"]["embed_error"] = _openai_error_detail(e)

    # 3) Chat — chamada minima (precisa da palavra 'json' nas messages)
    try:
        r = llm.chat_json(
            messages=[
                {"role": "system", "content": 'Responda apenas em json no formato {"ok": true}.'},
                {"role": "user", "content": "ping"},
            ],
            temperature=0,
        )
        out["openai"]["chat_ok"] = True
        out["openai"]["chat_sample"] = r
    except Exception as e:
        traceback.print_exc()
        out["openai"]["chat_ok"] = False
        out["openai"]["chat_error"] = _openai_error_detail(e)

    return out


# ---------------------------------------------------------------------------
# Autenticacao opcional contra a API CEFIS
# ---------------------------------------------------------------------------


@app.post("/api/auth/login")
async def auth_login(req: LoginRequest, response: Response) -> dict:
    """Faz login na CEFIS e guarda a key num cookie httpOnly do nosso dominio."""
    try:
        data = await cefis_api.login(req.email, req.password)
    except cefis_api.CefisAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))

    key = data.get("key")
    user = data.get("user") or {}
    if not key:
        raise HTTPException(status_code=500, detail="Resposta inesperada da CEFIS")

    response.set_cookie(
        SESSION_COOKIE,
        key,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # 30 dias
    )
    return {
        "logged_in": True,
        "user": {
            "id": user.get("id"),
            "name": user.get("name"),
            "first_name": user.get("first_name"),
            "email": user.get("email"),
            "avatar": user.get("avatar"),
            "is_premium": user.get("is_premium", False),
        },
    }


@app.post("/api/auth/logout")
async def auth_logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE)
    return {"logged_in": False}


@app.get("/api/me")
async def auth_me(cefis_key: str | None = Cookie(default=None, alias=SESSION_COOKIE)) -> dict:
    """Retorna o usuario autenticado + lista resumida de certificados conquistados."""
    if not cefis_key:
        return {"logged_in": False}
    try:
        user = await cefis_api.me(cefis_key)
        certs = await cefis_api.certificates(cefis_key, count=50)
    except cefis_api.CefisAuthError:
        return {"logged_in": False, "error": "session_expired"}

    completed_ids = sorted({c.get("courseId") for c in certs if c.get("courseId")})
    return {
        "logged_in": True,
        "user": {
            "id": user.get("id"),
            "name": user.get("name"),
            "first_name": user.get("first_name"),
            "email": user.get("email"),
            "avatar": user.get("avatar"),
            "occupation": user.get("occupation"),
            "is_premium": user.get("is_premium", False),
            "activities": user.get("activities", []),
        },
        "completed_course_ids": completed_ids,
    }


@app.post("/api/onboarding")
async def onboarding(
    req: OnboardingRequest,
    cefis_key: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> dict:
    """Gera diagnostico + plano de estudos a partir do perfil.

    Se o aluno estiver logado, ignora cursos ja concluidos e enriquece o
    prompt com a profissao real."""
    status_now = db.index_status()
    if not status_now.get("embeddings"):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "index_not_ready",
                "message": "Indice ainda sendo gerado. Tente novamente em alguns minutos.",
                "status": status_now,
            },
        )

    # Se logado, puxa certificados ja conquistados para nao recomendar repetido
    completed_ids: set[int] = set()
    extra_profile: dict = {}
    in_progress_lessons: list[dict] = []  # aulas que o aluno comecou mas nao terminou
    if cefis_key:
        try:
            user = await cefis_api.me(cefis_key)
            certs = await cefis_api.certificates(cefis_key, count=50)
            completed_ids = {c.get("courseId") for c in certs if c.get("courseId")}
            extra_profile = {
                "ocupacao": user.get("occupation"),
                "areas_cefis": user.get("activities") or [],
                "premium": user.get("is_premium"),
                "cursos_ja_concluidos": len(completed_ids),
            }
        except cefis_api.CefisAuthError:
            pass

    # 1) Recupera cursos candidatos
    excluded_courses = set(completed_ids) | set(req.exclude_course_ids or [])

    if req.course_ids:
        # Aluno escolheu manualmente os cursos -> usa exatamente esses
        with db.db_cursor() as cur:
            placeholders = ",".join("?" * len(req.course_ids))
            cur.execute(
                f"""SELECT id, title, subtitle, summary, keywords, duration,
                          lesson_count, average_rating, teacher_name, categories
                   FROM courses WHERE id IN ({placeholders})""",
                req.course_ids,
            )
            candidates = [dict(r) for r in cur.fetchall()]
    else:
        try:
            query_emb = llm.embed(f"{req.goal}\n\nNivel: {req.level}")
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=502, detail={"step": "embed_goal", **_openai_error_detail(e)})
        candidates = db.search_courses_by_embedding(query_emb, limit=30)
        if not candidates:
            candidates = db.search_courses_by_text(req.goal, limit=30)
        candidates = [c for c in candidates if c["id"] not in excluded_courses][:15]

    # 1b) Se logado, busca progresso real das aulas dos top-3 cursos candidatos.
    # Permite o tutor sugerir "continue de onde parou".
    if cefis_key and candidates:
        import asyncio
        try:
            top_ids = [c["id"] for c in candidates[:3]]
            results = await asyncio.gather(
                *(cefis_api.course_lessons_with_progress(cid, cefis_key) for cid in top_ids),
                return_exceptions=True,
            )
            for cid, lessons_with_p in zip(top_ids, results):
                if isinstance(lessons_with_p, Exception):
                    continue
                for ll in lessons_with_p or []:
                    prog = ll.get("progress") or {}
                    pct = prog.get("percentage") or 0
                    if 5 < pct < 90:  # em andamento (nao novo, nao concluido)
                        course_title = next(
                            (c["title"] for c in candidates if c["id"] == cid), ""
                        )
                        in_progress_lessons.append(
                            {
                                "course_id": cid,
                                "course_title": course_title,
                                "lesson_id": ll.get("id"),
                                "lesson_title": ll.get("title"),
                                "percentage": pct,
                                "last_second": prog.get("lastSecond"),
                            }
                        )
        except Exception as e:
            print(f"[progress] {e}")

    # 2) Diagnostico
    diag_payload = {
        "perfil": {
            "nome": req.name,
            "areas_interesse_ids": req.areas,
            "nivel": req.level,
            "tempo_disponivel_minutos": req.minutes,
            **extra_profile,
        },
        "objetivo": req.goal,
        "fase_da_sessao": req.phase,
        "historico_aluno": req.historico_resumo or {},
        "aulas_em_andamento": in_progress_lessons[:5] if in_progress_lessons else [],
        "cursos_disponiveis": [
            {
                "id": c["id"],
                "title": c["title"],
                "subtitle": c.get("subtitle"),
                "summary": (c.get("summary") or "")[:400],
                "duration_minutes": (c.get("duration") or 0) // 60,
                "rating": c.get("average_rating"),
            }
            for c in candidates
        ],
    }
    try:
        diagnosis = llm.chat_json(
            messages=[
                {"role": "system", "content": prompts.DIAGNOSIS_SYSTEM},
                {"role": "user", "content": json.dumps(diag_payload, ensure_ascii=False)},
            ]
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail={"step": "diagnosis_llm", **_openai_error_detail(e)})

    # 3) Carrega aulas dos cursos sugeridos
    course_ids = []
    for t in diagnosis.get("topics", []):
        for cid in t.get("course_ids", []):
            if cid not in course_ids:
                course_ids.append(cid)
    # se aluno restringiu cursos, respeita
    if req.course_ids:
        course_ids = [c for c in course_ids if c in req.course_ids] or req.course_ids
    course_ids = course_ids[:8]
    lessons = db.lessons_for_courses(course_ids)

    # Remove aulas ja vistas no historico
    excluded_lessons = set(req.exclude_lesson_ids or [])
    if excluded_lessons:
        lessons = [l for l in lessons if l["id"] not in excluded_lessons]

    # 4) Plano final
    plan_payload = {
        "perfil": diag_payload["perfil"],
        "objetivo": req.goal,
        "tempo_disponivel_minutos": req.minutes,
        "fase": req.phase,
        "fase_diretriz": (
            "Esta e a fase inicial - cubra os fundamentos."
            if req.phase == 1
            else f"Esta e a fase {req.phase} de aprofundamento. O aluno ja"
            f" estudou {len(excluded_lessons)} aulas anteriores - evite repetir"
            " conceitos basicos e avance para topicos mais profundos ou aplicados."
        ),
        "topicos": diagnosis.get("topics", []),
        "aulas_disponiveis": [
            {
                "lesson_id": l["id"],
                "course_id": l["course_id"],
                "course_title": l["course_title"],
                "title": l["title"],
                "teacher": l["teacher_name"],
                "duration_minutes": max(1, (l["duration"] or 0) // 60),
            }
            for l in lessons
        ],
    }
    try:
        plan = llm.chat_json(
            messages=[
                {"role": "system", "content": prompts.PLAN_SYSTEM},
                {"role": "user", "content": json.dumps(plan_payload, ensure_ascii=False)},
            ]
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail={"step": "plan_llm", **_openai_error_detail(e)})

    # 5) Enriquece itens do plano com URL real + aulas relacionadas
    items_out = []
    by_lesson = {l["id"]: l for l in lessons}
    for it in plan.get("items", []):
        lesson = by_lesson.get(it.get("lesson_id"))
        enriched = {
            **it,
            "course_url": (
                course_url(lesson["course_id"], lesson["course_title"])
                if lesson else None
            ),
            "course_title": lesson["course_title"] if lesson else None,
            "teacher": lesson["teacher_name"] if lesson else None,
        }

        # Conteudo gerado pela IA (resumo/quiz) ganha referencia para aulas
        # reais relacionadas, para o aluno aprofundar.
        if it.get("type") in ("resumo", "quiz") and not lesson:
            query_text = (it.get("title") or "") + " " + (it.get("summary_content") or "")
            query_text = query_text.strip()
            if query_text:
                try:
                    emb = llm.embed(query_text)
                    related = db.lessons_by_embedding(emb, limit=2)
                    enriched["related_lessons"] = [
                        {
                            "lesson_id": r["lesson_id"],
                            "lesson_title": r["lesson_title"],
                            "course_id": r["course_id"],
                            "course_title": r["course_title"],
                            "teacher": r.get("teacher_name"),
                            "course_url": course_url(r["course_id"], r["course_title"]),
                        }
                        for r in related
                    ]
                except Exception as e:
                    print(f"[related_lessons error] {e}")

        items_out.append(enriched)

    return {
        "diagnosis": diagnosis.get("diagnosis"),
        "catalog_gap": diagnosis.get("catalog_gap", False),
        "topics": diagnosis.get("topics", []),
        "plan": items_out,
        "phase": req.phase,
        "excluded_lessons_count": len(excluded_lessons),
        "excluded_courses_count": len(excluded_courses),
    }


@app.get("/api/cefis-tracks")
async def list_cefis_tracks(
    cefis_key: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> dict:
    """Lista trilhas curadas pela CEFIS (atalho para o objetivo)."""
    try:
        items = await cefis_api.tracks(count=20, api_key=cefis_key)
    except Exception as e:
        print(f"[cefis-tracks] {e}")
        return {"tracks": [], "error": str(e)}
    out = []
    for t in items:
        out.append(
            {
                "id": t.get("id"),
                "name": t.get("name"),
                "description": (t.get("description") or "")[:300],
                "banner": t.get("banner"),
                "course_count": t.get("course_count"),
                "duration_minutes": (t.get("duration") or 0) // 60,
                "categories": t.get("categories") or [],
                "rating": t.get("rating"),
                "following": t.get("following", False),
            }
        )
    return {"tracks": out, "total": len(out)}


@app.get("/api/cefis-tracks/{track_id}")
async def get_cefis_track(
    track_id: int,
    cefis_key: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> dict:
    """Detalhe de uma trilha CEFIS, com os course_ids para o tutor usar."""
    detail = await cefis_api.track_detail(track_id, api_key=cefis_key)
    if not detail:
        raise HTTPException(status_code=404, detail="Trilha nao encontrada")
    courses = detail.get("courses") or []
    course_ids = [c["id"] for c in courses if c.get("id")]
    return {
        "id": detail.get("id"),
        "name": detail.get("name"),
        "description": detail.get("description"),
        "course_count": len(courses),
        "course_ids": course_ids,
        "courses": [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "duration_minutes": (c.get("duration") or 0) // 60,
                "teacher": (c.get("teacher") or {}).get("name"),
            }
            for c in courses
        ],
    }


@app.post("/api/courses/search")
async def courses_search(req: CoursesSearchRequest) -> dict:
    """Busca semantica de cursos para o objetivo. Usado pela tela de selecao
    antes do aluno gerar o plano (deixa ele moldar)."""
    status_now = db.index_status()
    if not status_now.get("embeddings"):
        raise HTTPException(status_code=503, detail="Indice nao pronto")

    try:
        emb = llm.embed(f"{req.goal}\n\nNivel: {req.level}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail={"step": "embed", **_openai_error_detail(e)})
    found = db.search_courses_by_embedding(emb, limit=req.limit + len(req.exclude_course_ids) + 5)
    if not found:
        found = db.search_courses_by_text(req.goal, limit=req.limit + 5)

    exclude = set(req.exclude_course_ids or [])
    filtered = [c for c in found if c["id"] not in exclude][: req.limit]
    return {
        "courses": [
            {
                "id": c["id"],
                "title": c["title"],
                "subtitle": c.get("subtitle"),
                "summary": (c.get("summary") or "")[:280],
                "duration_minutes": (c.get("duration") or 0) // 60,
                "lesson_count": c.get("lesson_count"),
                "rating": c.get("average_rating"),
                "teacher": c.get("teacher_name"),
                "course_url": course_url(c["id"], c["title"]),
            }
            for c in filtered
        ],
        "total": len(filtered),
    }


@app.post("/api/tts")
async def tts(req: TTSRequest) -> StreamingResponse:
    """Converte texto em MP3 (streaming) via OpenAI TTS."""
    def audio_iter():
        try:
            yield from llm.tts_stream(req.text, voice=req.voice)
        except Exception as e:
            # se algo falhar no meio, encerra silenciosamente
            print(f"[tts error] {type(e).__name__}: {e}")
            return

    return StreamingResponse(
        audio_iter(),
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/api/quiz/{lesson_id}")
async def quiz(lesson_id: int) -> dict:
    """Gera 5 perguntas multipla escolha a partir da transcricao da aula."""
    chunks = db.chunks_for_lesson(lesson_id, limit=80)
    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="Aula nao encontrada ou sem transcricao indexada",
        )

    lesson_title = chunks[0]["lesson_title"]
    course_title = chunks[0]["course_title"]
    course_id = chunks[0]["course_id"]
    teacher = chunks[0].get("teacher_name")

    # concatena ate ~12k caracteres da transcricao
    content_parts: list[str] = []
    total = 0
    for ch in chunks:
        t = ch["text"]
        if total + len(t) > 12000:
            break
        content_parts.append(t)
        total += len(t)
    content = " ".join(content_parts)

    payload = {
        "curso": course_title,
        "aula": lesson_title,
        "transcricao": content,
    }
    result = llm.chat_json(
        messages=[
            {"role": "system", "content": prompts.QUIZ_SYSTEM},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=0.4,
    )
    questions = result.get("questions") or []
    # sanitize basico
    cleaned = []
    for q in questions:
        opts = q.get("options") or []
        ci = q.get("correct_index")
        if (
            isinstance(q.get("question"), str)
            and isinstance(opts, list)
            and len(opts) >= 2
            and isinstance(ci, int)
            and 0 <= ci < len(opts)
        ):
            cleaned.append(
                {
                    "question": q["question"].strip(),
                    "options": [str(o).strip() for o in opts],
                    "correct_index": ci,
                    "explanation": (q.get("explanation") or "").strip(),
                }
            )

    if not cleaned:
        raise HTTPException(
            status_code=502,
            detail="Modelo nao retornou perguntas validas",
        )

    return {
        "lesson_id": lesson_id,
        "lesson_title": lesson_title,
        "course_id": course_id,
        "course_title": course_title,
        "teacher": teacher,
        "questions": cleaned,
    }


@app.post("/api/roleplay")
async def roleplay(req: RoleplayRequest) -> StreamingResponse:
    """Simulacao de papel: tutor interpreta um personagem do cenario.
    SSE streaming igual ao chat."""
    sys = prompts.ROLEPLAY_SYSTEM + "\n\nCENARIO DA SIMULACAO:\n" + req.cenario
    messages: list[dict] = [{"role": "system", "content": sys}]
    for m in req.mensagens[-20:]:
        if m.get("role") in ("user", "assistant"):
            messages.append({"role": m["role"], "content": str(m.get("content", ""))[:2000]})

    def event_stream():
        try:
            for token in llm.chat_stream(messages, temperature=0.8):
                yield f"event: token\ndata: {json.dumps({'t': token}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/roleplay/feedback")
async def roleplay_feedback(req: RoleplayFeedbackRequest) -> dict:
    """Avalia a simulacao e retorna feedback estruturado + aulas relacionadas."""
    transcript = "CENARIO:\n" + req.cenario + "\n\nDIALOGO:\n"
    for m in req.mensagens:
        role = m.get("role", "user")
        speaker = "ALUNO" if role == "user" else "PERSONAGEM"
        transcript += f"{speaker}: {str(m.get('content',''))[:2000]}\n\n"

    try:
        fb = llm.chat_json(
            messages=[
                {"role": "system", "content": prompts.ROLEPLAY_FEEDBACK_SYSTEM},
                {"role": "user", "content": transcript[:8000]},
            ],
            temperature=0.3,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail={"step": "feedback_llm", **_openai_error_detail(e)})

    # Enriquece com aulas reais relacionadas aos topicos sugeridos
    aulas_recomendadas_keys = fb.get("aulas_recomendadas") or []
    aulas_links: list[dict] = []
    if aulas_recomendadas_keys:
        query = " ".join(aulas_recomendadas_keys) + " " + req.cenario
        try:
            emb = llm.embed(query)
            related = db.lessons_by_embedding(emb, limit=3)
            aulas_links = [
                {
                    "lesson_id": r["lesson_id"],
                    "lesson_title": r["lesson_title"],
                    "course_id": r["course_id"],
                    "course_title": r["course_title"],
                    "course_url": course_url(r["course_id"], r["course_title"]),
                }
                for r in related
            ]
        except Exception:
            pass

    return {
        "nota": fb.get("nota"),
        "resumo": fb.get("resumo"),
        "pontos_fortes": fb.get("pontos_fortes") or [],
        "pontos_melhoria": fb.get("pontos_melhoria") or [],
        "aulas_recomendadas_keys": aulas_recomendadas_keys,
        "aulas_links": aulas_links,
    }


@app.post("/api/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    """SSE streaming. Cada linha 'data: ...' e um pedaco de resposta ou metadata."""
    status_now = db.index_status()
    if not status_now.get("embeddings"):
        raise HTTPException(status_code=503, detail="Indice ainda nao pronto")

    q_emb = llm.embed(req.message)
    chunks = db.rag_search(q_emb, k=6)

    # contexto pra IA
    context_block = "\n\n".join(
        f"[{i+1}] Curso: {c['course_title']} | Aula: {c['lesson_title']} "
        f"(seg {c['start_seconds']})\n{c['text']}"
        for i, c in enumerate(chunks)
    )
    fontes = [
        {
            "curso": c["course_title"],
            "course_id": c["course_id"],
            "course_url": course_url(c["course_id"], c["course_title"]),
            "aula": c["lesson_title"],
            "lesson_id": c["lesson_id"],
            "segundo": c["start_seconds"],
        }
        for c in chunks
    ]

    sys = (
        prompts.CHAT_SYSTEM
        + "\n\nTrechos disponiveis das aulas:\n"
        + (context_block or "(nenhum trecho com similaridade alta)")
    )
    messages = [{"role": "system", "content": sys}]
    for h in req.history[-10:]:
        if h.get("role") in ("user", "assistant"):
            messages.append({"role": h["role"], "content": h.get("content", "")})
    messages.append({"role": "user", "content": req.message})

    def event_stream():
        # primeiro evento: lista de fontes (front-end usa pra renderizar citacoes)
        yield f"event: sources\ndata: {json.dumps(fontes, ensure_ascii=False)}\n\n"
        try:
            for token in llm.chat_stream(messages):
                yield f"event: token\ndata: {json.dumps({'t': token}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.environ.get("APP_HOST", "0.0.0.0"),
        port=int(os.environ.get("APP_PORT", 8000)),
        reload=True,
    )
