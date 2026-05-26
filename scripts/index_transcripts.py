"""
Indexador de transcricoes CEFIS para o Tutor IA.

Le os cursos extraidos em Docs/output/, parseia os VTTs, faz chunking por janela
de tempo, gera embeddings via OpenAI e salva tudo num SQLite com sqlite-vec.

Idempotente: pode ser interrompido e retomado. Mantem progresso em
data/index_state.json.

Uso:
    python scripts/index_transcripts.py [--reset] [--limit N]

Variaveis de ambiente (.env):
    OPENAI_API_KEY            obrigatorio
    OPENAI_EMBEDDING_MODEL    default text-embedding-3-small
    CEFIS_DATA_DIR            default ./Docs/output
    CEFIS_DB_PATH             default ./data/cefis.db
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import sqlite_vec
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Janela de tempo em segundos para agrupar legendas num unico chunk.
# Trade-off: mais curto = recall melhor, mais embeddings (custo). 60s e bom default.
CHUNK_WINDOW_SECONDS = 60
EMBEDDING_DIM = 1536  # text-embedding-3-small
BATCH_SIZE = 100      # max de inputs por chamada de embeddings


# ----------------------------------------------------------------------------
# Parser VTT
# ----------------------------------------------------------------------------

VTT_TIMESTAMP_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
)


def _ts_to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


@dataclass
class VttCue:
    start: float
    end: float
    text: str


def parse_vtt(path: Path) -> list[VttCue]:
    """Parse simples de WebVTT. Ignora cabecalho e tags de estilo."""
    cues: list[VttCue] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return cues

    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = VTT_TIMESTAMP_RE.search(line)
        if m:
            start = _ts_to_seconds(m.group(1), m.group(2), m.group(3), m.group(4))
            end = _ts_to_seconds(m.group(5), m.group(6), m.group(7), m.group(8))
            text_lines: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip():
                t = lines[i].strip()
                # remove o tracinho do inicio que o CEFIS coloca ("- texto")
                if t.startswith("- "):
                    t = t[2:]
                text_lines.append(t)
                i += 1
            text = " ".join(text_lines).strip()
            if text:
                cues.append(VttCue(start=start, end=end, text=text))
        i += 1
    return cues


@dataclass
class Chunk:
    course_id: int
    lesson_id: int
    start_seconds: int
    end_seconds: int
    text: str


def chunks_from_cues(
    cues: list[VttCue],
    course_id: int,
    lesson_id: int,
    window: int = CHUNK_WINDOW_SECONDS,
) -> list[Chunk]:
    """Agrupa cues em janelas de `window` segundos."""
    if not cues:
        return []
    out: list[Chunk] = []
    buf_text: list[str] = []
    buf_start: float = cues[0].start
    buf_end: float = cues[0].end
    for c in cues:
        # se passou da janela, fecha chunk
        if c.start - buf_start >= window and buf_text:
            out.append(
                Chunk(
                    course_id=course_id,
                    lesson_id=lesson_id,
                    start_seconds=int(buf_start),
                    end_seconds=int(buf_end),
                    text=" ".join(buf_text),
                )
            )
            buf_text = []
            buf_start = c.start
        buf_text.append(c.text)
        buf_end = c.end
    if buf_text:
        out.append(
            Chunk(
                course_id=course_id,
                lesson_id=lesson_id,
                start_seconds=int(buf_start),
                end_seconds=int(buf_end),
                text=" ".join(buf_text),
            )
        )
    return out


# ----------------------------------------------------------------------------
# Banco
# ----------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    subtitle TEXT,
    summary TEXT,
    keywords TEXT,
    duration INTEGER,
    lesson_count INTEGER,
    average_rating REAL,
    categories TEXT,  -- JSON array
    teacher_name TEXT,
    banner TEXT
);

CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    title TEXT NOT NULL,
    duration INTEGER,
    has_transcript INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
CREATE INDEX IF NOT EXISTS idx_lessons_course ON lessons(course_id);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    lesson_id INTEGER NOT NULL,
    start_seconds INTEGER NOT NULL,
    end_seconds INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedded INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_chunks_lesson ON chunks(lesson_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedded ON chunks(embedded);
"""


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.executescript(SCHEMA)
    # virtual table de embeddings (sqlite-vec)
    conn.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS chunk_embeddings "
        f"USING vec0(chunk_id INTEGER PRIMARY KEY, embedding FLOAT[{EMBEDDING_DIM}])"
    )
    conn.commit()
    return conn


def reset_db(db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()


# ----------------------------------------------------------------------------
# Ingest de metadados + chunks (sem embeddings ainda)
# ----------------------------------------------------------------------------


def ingest_catalog(conn: sqlite3.Connection, data_dir: Path, limit: int | None = None) -> int:
    """Le todos os details.json + VTTs e enche `courses`, `lessons`, `chunks`.
    Retorna quantos chunks novos foram criados."""
    course_dirs = sorted([p for p in data_dir.iterdir() if p.is_dir()])
    if limit:
        course_dirs = course_dirs[:limit]

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM chunks")
    chunks_before = cur.fetchone()[0]

    for cdir in tqdm(course_dirs, desc="Cursos"):
        cdetails_path = cdir / "details.json"
        if not cdetails_path.exists():
            continue
        try:
            cdetails = json.loads(cdetails_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        cdata = cdetails.get("data") or cdetails
        course_id = int(cdir.name)
        teacher = (cdata.get("teacher") or {}).get("name")
        cur.execute(
            """INSERT OR REPLACE INTO courses
               (id, title, subtitle, summary, keywords, duration, lesson_count,
                average_rating, categories, teacher_name, banner)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                course_id,
                cdata.get("title") or "",
                cdata.get("subtitle"),
                cdata.get("summary"),
                cdata.get("keywords"),
                cdata.get("duration"),
                cdata.get("lessonCount"),
                cdata.get("averageRating"),
                json.dumps(cdata.get("categories") or []),
                teacher,
                cdata.get("banner"),
            ),
        )

        lessons_dir = cdir / "lessons"
        if not lessons_dir.exists():
            continue
        for ldir in sorted(lessons_dir.iterdir(), key=lambda p: int(p.name) if p.name.isdigit() else 0):
            if not ldir.is_dir():
                continue
            ldetails_path = ldir / "details.json"
            if not ldetails_path.exists():
                continue
            try:
                ldata = json.loads(ldetails_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue

            lesson_id = int(ldata.get("id") or 0)
            if not lesson_id:
                continue
            # CEFIS usa duas convencoes: subtitle_pt.vtt (mais antigo)
            # e subtitle_pt-BR.vtt (mais recente). Aceita ambos.
            vtt_path: Path | None = None
            for cand in ("subtitle_pt.vtt", "subtitle_pt-BR.vtt"):
                p = ldir / cand
                if p.exists():
                    vtt_path = p
                    break
            has_transcript = vtt_path is not None
            cur.execute(
                """INSERT OR REPLACE INTO lessons
                   (id, course_id, position, title, duration, has_transcript)
                   VALUES (?,?,?,?,?,?)""",
                (
                    lesson_id,
                    course_id,
                    ldata.get("position") or 0,
                    ldata.get("title") or "",
                    ldata.get("duration") or 0,
                    int(has_transcript),
                ),
            )

            if not has_transcript:
                continue

            # ja indexou essa aula? pula
            cur.execute("SELECT 1 FROM chunks WHERE lesson_id = ? LIMIT 1", (lesson_id,))
            if cur.fetchone():
                continue

            cues = parse_vtt(vtt_path)
            for ch in chunks_from_cues(cues, course_id, lesson_id):
                cur.execute(
                    """INSERT INTO chunks
                       (course_id, lesson_id, start_seconds, end_seconds, text, embedded)
                       VALUES (?,?,?,?,?,0)""",
                    (ch.course_id, ch.lesson_id, ch.start_seconds, ch.end_seconds, ch.text),
                )
        conn.commit()

    cur.execute("SELECT COUNT(*) FROM chunks")
    chunks_after = cur.fetchone()[0]
    return chunks_after - chunks_before


# ----------------------------------------------------------------------------
# Embeddings em batch
# ----------------------------------------------------------------------------


def _serialize_vec(vec: list[float]) -> bytes:
    """sqlite-vec aceita bytes little-endian de floats."""
    return struct.pack(f"{len(vec)}f", *vec)


def embed_pending(conn: sqlite3.Connection, client: OpenAI, model: str) -> None:
    """Le chunks ainda nao embedded, gera embedding e grava em chunk_embeddings."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM chunks WHERE embedded = 0")
    total_pending = cur.fetchone()[0]
    if total_pending == 0:
        print("Todos os chunks ja tem embedding. Nada a fazer.")
        return

    print(f"Gerando embeddings para {total_pending:,} chunks (batch={BATCH_SIZE})...")
    bar = tqdm(total=total_pending, desc="Embeddings", unit="chunk")
    try:
        while True:
            rows = cur.execute(
                "SELECT id, text FROM chunks WHERE embedded = 0 LIMIT ?",
                (BATCH_SIZE,),
            ).fetchall()
            if not rows:
                break

            ids = [r[0] for r in rows]
            texts = [r[1][:8000] for r in rows]  # truncar por seguranca

            # tentativas com backoff exponencial para 429 / 5xx
            attempt = 0
            while True:
                try:
                    resp = client.embeddings.create(model=model, input=texts)
                    break
                except Exception as e:
                    attempt += 1
                    if attempt > 5:
                        raise
                    delay = 2**attempt
                    print(f"\nErro {type(e).__name__}: {e} — retry em {delay}s")
                    time.sleep(delay)

            ins = conn.cursor()
            for chunk_id, item in zip(ids, resp.data):
                vec = item.embedding
                ins.execute(
                    "INSERT OR REPLACE INTO chunk_embeddings(chunk_id, embedding) VALUES (?, ?)",
                    (chunk_id, _serialize_vec(vec)),
                )
            ins.executemany(
                "UPDATE chunks SET embedded = 1 WHERE id = ?",
                [(i,) for i in ids],
            )
            conn.commit()
            bar.update(len(rows))
    finally:
        bar.close()


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="Apaga o DB e reindexa do zero")
    parser.add_argument("--limit", type=int, help="Processa apenas N cursos (debug)")
    parser.add_argument(
        "--no-embed",
        action="store_true",
        help="So faz a ingestao do catalogo/chunks, nao chama OpenAI",
    )
    args = parser.parse_args()

    load_dotenv()
    data_dir = Path(os.environ.get("CEFIS_DATA_DIR", "./Docs/output")).resolve()
    db_path = Path(os.environ.get("CEFIS_DB_PATH", "./data/cefis.db")).resolve()
    model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    if not data_dir.exists():
        print(f"ERRO: pasta de dados nao encontrada: {data_dir}", file=sys.stderr)
        return 2

    if args.reset:
        print(f"Resetando {db_path}")
        reset_db(db_path)

    conn = init_db(db_path)
    print(f"DB: {db_path}")
    print(f"Catalogo: {data_dir}")

    new_chunks = ingest_catalog(conn, data_dir, limit=args.limit)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM courses")
    n_courses = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM lessons")
    n_lessons = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM lessons WHERE has_transcript = 1")
    n_lessons_t = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM chunks")
    n_chunks = cur.fetchone()[0]
    print(
        f"Catalogo: {n_courses} cursos, {n_lessons} aulas "
        f"({n_lessons_t} com transcricao), {n_chunks} chunks (+{new_chunks} novos)"
    )

    if args.no_embed:
        print("--no-embed passado, parando antes da chamada OpenAI.")
        return 0

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-proj-COLE"):
        print(
            "ERRO: OPENAI_API_KEY ausente. Copie .env.example para .env e cole a chave.",
            file=sys.stderr,
        )
        return 3

    client = OpenAI(api_key=api_key)
    embed_pending(conn, client, model)

    # estado final
    cur.execute("SELECT COUNT(*) FROM chunk_embeddings")
    n_emb = cur.fetchone()[0]
    print(f"Pronto. {n_emb:,} embeddings no indice.")

    # salva estado
    state = {
        "courses": n_courses,
        "lessons": n_lessons,
        "lessons_with_transcript": n_lessons_t,
        "chunks": n_chunks,
        "embeddings": n_emb,
        "model": model,
        "embedding_dim": EMBEDDING_DIM,
        "chunk_window_seconds": CHUNK_WINDOW_SECONDS,
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    state_path = db_path.parent / "index_state.json"
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"Estado salvo em {state_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
