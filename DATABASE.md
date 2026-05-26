# Database

Estrutura do índice local (`data/cefis.db`) e como ele é populado.

---

## Visão geral

- **Engine:** SQLite 3 com extensão [`sqlite-vec`](https://github.com/asg017/sqlite-vec) para busca vetorial
- **Tamanho final:** ~260 MB com todo o catálogo indexado
- **Conteúdo:** catálogo CEFIS (cursos, aulas) + chunks de transcrição com embeddings 1536-dim
- **Caráter:** read-mostly em runtime, populado uma vez por `scripts/index_transcripts.py`

Estatísticas no momento da entrega:

| Tabela | Linhas |
|---|---|
| `courses` | 476 |
| `lessons` | 12.172 |
| `lessons` com transcrição | 7.447 |
| `chunks` | 34.422 |
| `chunk_embeddings` | 34.422 |

---

## Schema completo

```sql
CREATE TABLE courses (
    id              INTEGER PRIMARY KEY,
    title           TEXT NOT NULL,
    subtitle        TEXT,
    summary         TEXT,
    keywords        TEXT,
    duration        INTEGER,            -- segundos
    lesson_count    INTEGER,
    average_rating  REAL,
    categories      TEXT,               -- JSON array, ex: "[1,4]"
    teacher_name    TEXT,
    banner          TEXT                -- URL
);

CREATE TABLE lessons (
    id              INTEGER PRIMARY KEY,
    course_id       INTEGER NOT NULL,
    position        INTEGER NOT NULL,
    title           TEXT NOT NULL,
    duration        INTEGER,            -- segundos
    has_transcript  INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
CREATE INDEX idx_lessons_course ON lessons(course_id);

CREATE TABLE chunks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id       INTEGER NOT NULL,
    lesson_id       INTEGER NOT NULL,
    start_seconds   INTEGER NOT NULL,
    end_seconds     INTEGER NOT NULL,
    text            TEXT NOT NULL,
    embedded        INTEGER NOT NULL DEFAULT 0  -- 1 quando ja tem embedding
);
CREATE INDEX idx_chunks_lesson ON chunks(lesson_id);
CREATE INDEX idx_chunks_embedded ON chunks(embedded);

-- Tabela virtual do sqlite-vec
CREATE VIRTUAL TABLE chunk_embeddings USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding FLOAT[1536]
);
```

---

## Origem dos dados

Tudo vem do `Docs/output/` (descompactação de `Docs/courses.zip`):

```
Docs/output/
└── {course_id}/
    ├── details.json                          → courses(id, title, ...)
    └── lessons/
        └── {position}/
            ├── details.json                  → lessons(id, course_id, position, ...)
            ├── subtitle_pt.vtt    (~1.5k)    → chunks
            └── subtitle_pt-BR.vtt (~5.9k)    → chunks
```

O indexador aceita ambos os nomes de VTT (`subtitle_pt.vtt` para cursos antigos, `subtitle_pt-BR.vtt` para os mais recentes).

---

## Chunking de transcrições

Cada VTT é parseado em "cues" (blocos com timestamp + texto). Cues consecutivos são agrupados em **janelas de 60 segundos**:

```
Cue 1 (0:00 – 0:06): "Olá, pessoal..."
Cue 2 (0:06 – 0:11): "Hoje vamos falar..."
Cue 3 (0:11 – 0:17): "...do ciclo PDCA"
...                                              ← janela de 60s
Cue N (0:58 – 1:04): "...na próxima sessão"

→ 1 chunk com text = "Olá pessoal Hoje vamos falar... próxima sessão"
  start_seconds=0, end_seconds=64
```

Trade-off:
- **Menor janela (30s)** → recall melhor (mais granular), mais embeddings ($0.30)
- **60s (escolhido)** → equilibrado, ~$0.17 total
- **Maior (2 min)** → recall pior em respostas específicas

---

## Embeddings

- **Modelo:** OpenAI `text-embedding-3-small`
- **Dimensão:** 1536
- **Custo:** $0.02 / 1M tokens → ~$0.17 para 34.422 chunks (≈8.5M tokens)
- **Batch:** 100 textos por chamada à API
- **Retry:** backoff exponencial com 5 tentativas (`scripts/index_transcripts.py`)
- **Serialização:** floats little-endian via `struct.pack`, gravados no `BLOB` da virtual table

Em runtime:
- Query do aluno também é embedada
- `sqlite-vec` faz top-K com distância cosseno (`MATCH ?` + `AND k = ?`)
- Tempo de query: ~50ms para top-6 em 34k vetores

---

## Estado da indexação

Após `scripts/index_transcripts.py` terminar, gera `data/index_state.json`:

```json
{
  "courses": 476,
  "lessons": 12172,
  "lessons_with_transcript": 7447,
  "chunks": 34422,
  "embeddings": 34422,
  "model": "text-embedding-3-small",
  "embedding_dim": 1536,
  "chunk_window_seconds": 60,
  "finished_at": "2026-05-26T11:58:45"
}
```

A UI lê via `GET /api/status` para mostrar barra de progresso enquanto indexa.

---

## Queries-chave do runtime

### 1. Top-K cursos por similaridade (`db.search_courses_by_embedding`)

Usado no `/api/onboarding` e `/api/courses/search`. Agrupa por curso a partir dos top-100 chunks mais próximos:

```sql
SELECT c.id, c.title, c.subtitle, c.summary, c.keywords, c.duration,
       c.lesson_count, c.average_rating, c.teacher_name, c.categories,
       AVG(ce.distance) AS avg_dist,
       COUNT(*) AS hits
FROM chunk_embeddings ce
JOIN chunks ch ON ch.id = ce.chunk_id
JOIN courses c ON c.id = ch.course_id
WHERE ce.embedding MATCH ?
  AND k = 100
GROUP BY c.id
ORDER BY avg_dist ASC
LIMIT 15;
```

### 2. Top-K chunks para RAG (`db.rag_search`)

Usado no chat. Top-6 chunks com metadata para citação:

```sql
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
  AND k = 6
ORDER BY ce.distance;
```

### 3. Aulas por curso (`db.lessons_for_courses`)

Usado para montar o plano. Pega todas as aulas dos cursos sugeridos pelo diagnóstico:

```sql
SELECT l.id, l.course_id, l.position, l.title, l.duration,
       l.has_transcript, c.title AS course_title, c.teacher_name
FROM lessons l
JOIN courses c ON c.id = l.course_id
WHERE l.course_id IN (?, ?, ?, ...)
ORDER BY l.course_id, l.position;
```

### 4. Aulas relacionadas a um resumo (`db.lessons_by_embedding`)

Usado para enriquecer cada item `resumo` do plano com referência à aula real:

```sql
SELECT l.id AS lesson_id, l.title AS lesson_title,
       c.id AS course_id, c.title AS course_title, c.teacher_name,
       AVG(ce.distance) AS avg_dist, COUNT(*) AS hits
FROM chunk_embeddings ce
JOIN chunks ch ON ch.id = ce.chunk_id
JOIN lessons l ON l.id = ch.lesson_id
JOIN courses c ON c.id = ch.course_id
WHERE ce.embedding MATCH ?
  AND k = 30
GROUP BY l.id
ORDER BY avg_dist ASC
LIMIT 2;
```

### 5. Chunks de uma aula (`db.chunks_for_lesson`)

Usado para gerar quiz. Todos os chunks da aula em ordem cronológica:

```sql
SELECT ch.id, ch.text, ch.start_seconds, ch.end_seconds,
       l.title AS lesson_title, l.duration AS lesson_duration,
       c.id AS course_id, c.title AS course_title, c.teacher_name
FROM chunks ch
JOIN lessons l ON l.id = ch.lesson_id
JOIN courses c ON c.id = ch.course_id
WHERE ch.lesson_id = ?
ORDER BY ch.start_seconds
LIMIT 80;
```

---

## Categorias (inferidas do catálogo)

A documentação do dev fala em `categories: 1-7` mas não nomeia. Analisando as 699 ocorrências de `categories[]` em todos os cursos:

| ID | Nome (inferido) | Cursos | Amostras |
|----|---|---|---|
| 1 | Fiscal & Tributário | 215 | Direito Tributário, NCM, IPO, ICMS |
| 2 | Contábil | 203 | IFRS, CPC, DVA, Ativo Imobilizado |
| 3 | Trabalhista & RH | 76 | Direito do Trabalho, Previdenciário |
| 4 | Gestão & Negócios | 123 | Canvas, Negociação, Inteligência Emocional |
| 5 | Processos & Estratégia | 56 | Six Sigma, Gestão de Processos |
| 6 | Desenvolvimento Pessoal | 24 | Storytelling, Home Office, Comunicação |
| 7 | Tecnologia & IA | 2 | IA para contadores |

Esses nomes aparecem no onboarding da UI (passo 1) e são usados para fazer match com `activities[]` do `/user/me` da API CEFIS quando o aluno faz login.

---

## Dados do cliente (localStorage)

Nada de PII no servidor — perfil e histórico vivem no browser:

```js
localStorage.cefis_perfil    // { name, areas[], goal, level, minutes }
localStorage.cefis_passo     // número (1, 2 ou 3) do wizard
localStorage.cefis_historico // {
                             //   lessons_concluidas: [42, 43, ...],
                             //   cursos_concluidos:  [1126, 1132, ...],
                             //   quizzes: [{lesson_id, course_id, acertos, total, ts}],
                             //   planos:  [{goal, phase, ts, items_count, completed}]
                             // }
```

Cookie httpOnly (gerenciado pelo backend):
```
cefis_key  -> API key da CEFIS quando o aluno faz login (opcional)
```

---

## Backup / migração

```bash
# Backup
cp data/cefis.db data/cefis.db.bkp

# Restaurar
cp data/cefis.db.bkp data/cefis.db
nssm restart TutorCEFIS  # se rodando como serviço
```

Reindexar do zero:
```cmd
indexar.bat --reset
```

---

## Limites conhecidos & roadmap

| Limite | Hoje | Plano v2 |
|---|---|---|
| Multi-instância (HA) | ❌ SQLite single-writer | Postgres + pgvector |
| Replicação | ❌ | Postgres streaming replication |
| Atualização incremental do catálogo | Manual via `--reset` | Job diário consumindo `/courses?status=...&filter=new` |
| Histórico de progresso server-side | ❌ só localStorage | Tabela `user_progress` com agregação |
| Multi-tenancy | ❌ | Schema por org, `tenant_id` em todas tabelas |

Detalhado em [PROXIMAS_FUNCIONALIDADES.md](PROXIMAS_FUNCIONALIDADES.md).
