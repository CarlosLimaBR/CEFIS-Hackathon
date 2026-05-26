# Arquitetura

Visão técnica do Tutor IA CEFIS: stack, fluxos, decisões.

---

## Stack em uma linha

**Python 3.11 + FastAPI + SQLite (sqlite-vec) + OpenAI** no backend.
**HTML + Tailwind CDN + Alpine.js** no frontend — **zero build**.

Deploy: Windows Server + IIS (URL Rewrite + ARR) + nssm + Let's Encrypt.

---

## Diagrama de arquitetura

```
                          ┌───────────────────────────────┐
                          │  Browser (Chrome/Firefox/...) │
                          │  SPA Alpine.js + Tailwind     │
                          └────────────┬──────────────────┘
                                       │ HTTPS
                                       ▼
                          ┌───────────────────────────────┐
                          │  IIS + URL Rewrite + ARR      │
                          │  Reverse proxy + TLS          │
                          │  (Let's Encrypt cert)         │
                          └────────────┬──────────────────┘
                                       │ HTTP local
                                       ▼
                          ┌───────────────────────────────┐
                          │  uvicorn :8000 (serviço nssm) │
                          │  FastAPI app                  │
                          └────┬──────────┬───────────┬───┘
                               │          │           │
                               ▼          ▼           ▼
                  ┌─────────────────┐ ┌──────────┐ ┌─────────────┐
                  │  SQLite + vec   │ │  OpenAI  │ │  API CEFIS  │
                  │  (índice local) │ │   API    │ │ (opcional)  │
                  └─────────────────┘ └──────────┘ └─────────────┘
                    34.422 chunks       embed       login + perfil
                    476 cursos          chat         certificados
                    12.172 aulas        tts          trilhas
                                                     progress real
```

---

## Fluxo principal — gerar um plano

```
1. Browser → POST /api/onboarding
   { name, areas, goal, level, minutes,
     course_ids?, exclude_lesson_ids[], phase }

2. Backend:
   a. (se logado) chama API CEFIS:
      - GET /user/me → ocupação, áreas declaradas
      - GET /performance/certificates → cursos já concluídos
      - GET /courses/:id/lessons → progresso real das aulas (asyncio.gather)
   b. llm.embed(goal) → vetor 1536d
   c. db.search_courses_by_embedding() → top-15 cursos candidatos
   d. Remove cursos já concluídos (do histórico CEFIS + localStorage)
   e. llm.chat_json(DIAGNOSIS_SYSTEM, payload) → diagnóstico + tópicos
   f. db.lessons_for_courses() → aulas relevantes
   g. Remove aulas já vistas (exclude_lesson_ids do client)
   h. llm.chat_json(PLAN_SYSTEM, payload) → plano (mistura aula + resumo)
   i. Para cada item type=resumo:
      - llm.embed(título) → busca aulas relacionadas (db.lessons_by_embedding)
      - Anexa "Para se aprofundar" com link real

3. Browser recebe JSON, renderiza plano + diagnóstico
```

---

## Fluxo do chat (RAG com SSE)

```
1. Browser → POST /api/chat
   { message, history[] }

2. Backend (StreamingResponse SSE):
   a. llm.embed(message) → vetor
   b. db.rag_search(vetor, k=6) → top-6 chunks por distância vetorial
   c. yield event:sources data:{[curso, aula, segundo, ...]}
   d. Monta contexto com os trechos
   e. llm.chat_stream(CHAT_SYSTEM + contexto + history + message)
      Para cada token recebido da OpenAI:
        yield event:token data:{"t": "..."}
   f. yield event:done data:{}

3. Browser parseia stream:
   - 'sources' → exibe lista de fontes clicáveis na bolha
   - 'token' → concatena no .texto da bolha do tutor (proxy reativo Alpine)
   - 'done' → fim, libera input
```

---

## Decisões de design

### 1. Por que catálogo local em vez de só API?

**Catálogo CEFIS vem pronto em `Docs/courses.zip`** (476 cursos + 7.447 transcrições VTT). Indexando localmente:
- Latência de busca semântica: ~50ms vs ~500ms+ da API
- Zero rate-limit
- Funciona offline depois de indexado
- Permite RAG profundo (chunks por aula) que a API REST não expõe

Trade-off aceito: dados podem ficar desatualizados. Aceitável para o hackathon (catálogo estável) e fácil de reindexar.

### 2. Por que SQLite + sqlite-vec em vez de Pinecone/Qdrant/pgvector?

- **Zero infra**: arquivo único, sem servidor de banco
- **Performance**: 50ms para top-K em 34k vetores num laptop
- **Portabilidade**: cabe num zip de 240MB pra mover entre servidores
- **Custo**: zero (vs $70/mês de Pinecone básico)

Limite conhecido: ruim para multi-instância (sem replicação). Para hackathon e POC, ótimo. Para produção em escala, [DATABASE.md](DATABASE.md) discute migração para Postgres+pgvector.

### 3. Por que sem framework de frontend?

- **Sem build**: copiar arquivos = deploy
- **Sem npm**: economia de 100MB de node_modules + cadeia de supply-chain
- **Tailwind CDN + Alpine.js**: dev como SPA real, mas sem build step
- **Sem service worker, sem PWA por padrão**: foco em entregar primeiro

### 4. Por que streaming SSE em vez de WebSocket?

- Unidirecional (servidor → cliente) é suficiente para chat
- Funciona em qualquer reverse proxy (não exige `Upgrade` header)
- Implementação trivial em FastAPI (`StreamingResponse`)
- Funciona com fetch + getReader() — sem dependência client

### 5. Por que persistência em localStorage (sem login obrigatório)?

- **Friction zero** para começar: aluno chega e usa imediatamente
- **Privacidade**: nenhum dado pessoal trafega para o servidor
- **Login CEFIS é opcional**: puxa progresso real quando o aluno escolhe entrar
- localStorage tem ~5 MB, suficiente para anos de histórico

---

## Endpoints (20 rotas)

### Públicos (não precisam de auth)

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | SPA estática (`index.html`) |
| `GET` | `/static/*` | Assets (logos, futuros JS/CSS) |
| `GET` | `/api/status` | Estado do índice |
| `GET` | `/api/diag` | Diagnóstico (env + conectividade OpenAI) |
| `POST` | `/api/onboarding` | Gera diagnóstico + plano (aceita login opcional via cookie) |
| `POST` | `/api/courses/search` | Lista cursos candidatos por similaridade |
| `POST` | `/api/chat` | Chat com RAG (SSE streaming) |
| `POST` | `/api/quiz/{lesson_id}` | Gera quiz de 5 perguntas da aula |
| `POST` | `/api/roleplay` | Simulação roleplay (SSE) — IA interpreta personagem |
| `POST` | `/api/roleplay/feedback` | Avaliação estruturada da simulação + aulas linkadas |
| `POST` | `/api/tts` | Texto → MP3 (streaming) |
| `GET` | `/api/cefis-tracks` | Trilhas oficiais (proxy GET /tracks da CEFIS) |
| `GET` | `/api/cefis-tracks/{id}` | Detalhe + course_ids de uma trilha CEFIS |

### Autenticação (cookie httpOnly opcional)

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/auth/login` | Login na API CEFIS, grava cookie |
| `POST` | `/api/auth/logout` | Remove cookie |
| `GET` | `/api/me` | Dados do usuário CEFIS + cursos certificados |

---

## Modelo de prompts

Todos os prompts vivem em [`app/prompts.py`](app/prompts.py) — fácil de revisar e A/B testar.

| Prompt | Modelo | Function | Quando |
|---|---|---|---|
| `DIAGNOSIS_SYSTEM` | `gpt-4o-mini` (JSON) | Diagnóstico de lacunas + tópicos | Onboarding |
| `PLAN_SYSTEM` | `gpt-4o-mini` (JSON) | Sequência de aulas + resumos respeitando tempo | Onboarding |
| `CHAT_SYSTEM` | `gpt-4o-mini` (streaming) | Resposta com RAG e citação | Chat |
| `QUIZ_SYSTEM` | `gpt-4o-mini` (JSON) | 5 perguntas múltipla escolha + explicação | Quiz |
| `ROLEPLAY_SYSTEM` | `gpt-4o-mini` (streaming, temp 0.8) | IA interpreta personagem do cenário | Roleplay |
| `ROLEPLAY_FEEDBACK_SYSTEM` | `gpt-4o-mini` (JSON) | Avaliação da simulação com nota/pontos/aulas | Roleplay |

**Regras anti-alucinação** (em todos os prompts):
- "Responda apenas em json válido seguindo o schema"
- "Não invente cursos/aulas que não estão na lista"
- "Cite a fonte como [curso: X, aula: Y, segundo: S]"
- "Se a info não está nos trechos, diga claramente 'não encontrei nas aulas processadas'"

---

## Indexação (offline)

Roda uma vez via `scripts/index_transcripts.py`:

```
1. Percorre Docs/output/{course_id}/
2. Lê details.json → INSERT INTO courses
3. Para cada lesson/{pos}/details.json:
   - INSERT INTO lessons
4. Se existe subtitle_pt.vtt OU subtitle_pt-BR.vtt:
   - Parse VTT (regex de timestamps)
   - chunks_from_cues(window=60s) → agrupa cues em janelas de 60s
   - INSERT INTO chunks (sem embedding)
5. Batch de 100 chunks → OpenAI embeddings
   - INSERT INTO chunk_embeddings (sqlite-vec virtual table)
   - UPDATE chunks SET embedded = 1
6. Repete até embedded = 0 sumir
7. Salva data/index_state.json com totais
```

Idempotente: pode interromper com `Ctrl+C` e rodar de novo. Custo total: ~$0.17. Tempo: 15-25 min.

Detalhes do schema em [DATABASE.md](DATABASE.md).

---

## Frontend (`app/static/index.html`)

Tudo em um arquivo HTML. Estado gerenciado por Alpine.js (`x-data="app()"`):

```js
function app() {
  return {
    tela: 'indexando' | 'onboarding' | 'selecao_cursos' | 'gerando' | 'plano',
    perfil: { name, areas[], goal, level, minutes },
    plano: [{ type, title, lesson_id, duration_minutes, concluido, ... }],
    conversas: [{ tipo: 'aluno'|'tutor', texto, fontes[] }],
    historico: { lessons_concluidas, cursos_concluidos, quizzes, planos },
    quizAtual: { ... },
    audioKey, audioEl, audioCache,
    novaSessao: { minutes, modo, ... },
    // ...
  };
}
```

Persistência:
- `localStorage.cefis_perfil` — perfil do aluno
- `localStorage.cefis_passo` — onde parou no wizard
- `localStorage.cefis_historico` — histórico cumulativo

Watchers Alpine: `$watch('perfil', ...)` e `$watch('historico', ...)` salvam automaticamente.

---

## Testes E2E

`scripts/test_endpoints.py` — 10 testes que batem direto nos endpoints HTTP:

```
 1. /api/status                  — índice pronto
 2. /api/onboarding              — gera diagnóstico + plano
 3. /api/chat (SSE)              — streaming + fontes
 4. /api/tts                     — MP3 binário
 5. /api/quiz/{id}               — 5 perguntas estruturadas
 6. /api/courses/search          — top-K cursos
 7. /api/onboarding multi-fase   — exclui aulas já vistas
 8. /api/cefis-tracks            — trilhas via API real
 9. /api/roleplay + feedback     — simulação + avaliação estruturada
10. resumos_com_ref              — related_lessons em todos resumos
```

Rodar contra local:
```cmd
.venv\Scripts\python.exe scripts\test_endpoints.py
```

Rodar contra produção:
```cmd
.venv\Scripts\python.exe scripts\test_endpoints.py https://tutor-cefis.duckdns.org
```

Validação manual no browser também foi feita via **Playwright headless** — abre Chrome real, percorre onboarding → plano → chat, captura DOM e valida que a resposta renderiza (incluindo correção de bug de reatividade Alpine).

---

## Próximos passos

- Schema do banco: [DATABASE.md](DATABASE.md)
- Como deployar: [DEPLOY.md](DEPLOY.md)
- Roadmap de v2: [PROXIMAS_FUNCIONALIDADES.md](PROXIMAS_FUNCIONALIDADES.md)
