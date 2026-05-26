"""Conexao com SQLite + sqlite-vec e helpers de busca semantica."""

from __future__ import annotations

import os
import sqlite3
import struct
from contextlib import contextmanager
from pathlib import Path

import sqlite_vec

DB_PATH = Path(os.environ.get("CEFIS_DB_PATH", "./data/cefis.db")).resolve()


def get_connection() -> sqlite3.Connection:
    """Conexao com a extensao sqlite-vec ja carregada."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        yield conn.cursor()
    finally:
        conn.close()


def serialize_vec(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def index_status() -> dict:
    """Resumo do estado do indice — usado pela UI para mostrar progresso."""
    with db_cursor() as cur:
        try:
            cur.execute("SELECT COUNT(*) FROM courses")
            courses = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM lessons")
            lessons = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM lessons WHERE has_transcript = 1")
            lessons_t = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM chunks")
            chunks = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM chunks WHERE embedded = 1")
            embedded = cur.fetchone()[0]
        except sqlite3.OperationalError:
            return {"ready": False, "reason": "DB nao inicializado"}
    return {
        "ready": embedded > 0,
        "courses": courses,
        "lessons": lessons,
        "lessons_with_transcript": lessons_t,
        "chunks": chunks,
        "embeddings": embedded,
        "progress": round(embedded / chunks, 3) if chunks else 0,
    }


def search_courses_by_text(query: str, limit: int = 20) -> list[dict]:
    """Busca textual simples (LIKE) em title/subtitle/summary/keywords.
    Usada como pre-filtro antes de chamar a IA para diagnostico/plano."""
    like = f"%{query.lower()}%"
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT id, title, subtitle, summary, keywords, duration, lesson_count,
                   average_rating, teacher_name, categories
            FROM courses
            WHERE lower(title) LIKE ?
               OR lower(subtitle) LIKE ?
               OR lower(summary) LIKE ?
               OR lower(keywords) LIKE ?
            ORDER BY average_rating DESC NULLS LAST
            LIMIT ?
            """,
            (like, like, like, like, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def search_courses_by_embedding(
    query_embedding: list[float], limit: int = 20
) -> list[dict]:
    """Busca semantica via aggregacao por curso dos chunks mais proximos.

    Estrategia: pega top-100 chunks proximos da query, agrupa por curso,
    pondera pela similaridade media (peso negativo da distancia).
    """
    blob = serialize_vec(query_embedding)
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.title, c.subtitle, c.summary, c.keywords, c.duration,
                   c.lesson_count, c.average_rating, c.teacher_name, c.categories,
                   AVG(ce.distance) as avg_dist, COUNT(*) as hits
            FROM chunk_embeddings ce
            JOIN chunks ch ON ch.id = ce.chunk_id
            JOIN courses c ON c.id = ch.course_id
            WHERE ce.embedding MATCH ?
              AND k = 100
            GROUP BY c.id
            ORDER BY avg_dist ASC
            LIMIT ?
            """,
            (blob, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def lessons_for_courses(course_ids: list[int]) -> list[dict]:
    if not course_ids:
        return []
    placeholders = ",".join("?" * len(course_ids))
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT l.id, l.course_id, l.position, l.title, l.duration,
                   l.has_transcript, c.title AS course_title, c.teacher_name
            FROM lessons l
            JOIN courses c ON c.id = l.course_id
            WHERE l.course_id IN ({placeholders})
            ORDER BY l.course_id, l.position
            """,
            course_ids,
        )
        return [dict(r) for r in cur.fetchall()]


def chunks_for_lesson(lesson_id: int, limit: int = 80) -> list[dict]:
    """Todos os chunks de uma aula, em ordem cronologica. Usado pelo gerador
    de quiz para ter o material completo da aula."""
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT ch.id, ch.text, ch.start_seconds, ch.end_seconds,
                   l.title AS lesson_title, l.duration AS lesson_duration,
                   c.id AS course_id, c.title AS course_title,
                   c.teacher_name
            FROM chunks ch
            JOIN lessons l ON l.id = ch.lesson_id
            JOIN courses c ON c.id = ch.course_id
            WHERE ch.lesson_id = ?
            ORDER BY ch.start_seconds
            LIMIT ?
            """,
            (lesson_id, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def rag_search(query_embedding: list[float], k: int = 6) -> list[dict]:
    """Top-K chunks mais proximos da query - usado pelo chat."""
    blob = serialize_vec(query_embedding)
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT ch.id, ch.course_id, ch.lesson_id, ch.start_seconds,
                   ch.end_seconds, ch.text,
                   c.title AS course_title, l.title AS lesson_title,
                   l.position AS lesson_position,
                   ce.distance
            FROM chunk_embeddings ce
            JOIN chunks ch ON ch.id = ce.chunk_id
            JOIN courses c ON c.id = ch.course_id
            JOIN lessons l ON l.id = ch.lesson_id
            WHERE ce.embedding MATCH ?
              AND k = ?
            ORDER BY ce.distance
            """,
            (blob, k),
        )
        return [dict(r) for r in cur.fetchall()]
