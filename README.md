# Tutor IA CEFIS

Tutor de aprendizado personalizado feito para o **Hackathon de Inovação em Aprendizado da CEFIS** (26/05/2026).

Onboarding curto, diagnóstico de lacunas, plano de estudos cronometrado usando o catálogo real e chat de dúvidas com RAG sobre as transcrições das aulas.

---

## Como funciona

- **Onboarding (3 passos)** — perfil, objetivo livre, nível e tempo disponível.
- **Diagnóstico de lacunas** — IA cruza o objetivo com o catálogo CEFIS e descreve o gap do aluno.
- **Plano de estudos** — sequência ordenada de aulas reais + resumos da IA, respeitando o tempo declarado.
- **Chat com RAG** — perguntas livres respondidas com base no texto das aulas, citando curso/aula/segundo.

Stack: **Python + FastAPI + SQLite + sqlite-vec + OpenAI**. Frontend HTML estático com Tailwind via CDN e Alpine.js (zero build).

---

## Pré-requisitos

- **Python 3.11+** ([python.org/downloads](https://www.python.org/downloads/)).
- Pasta `Docs/output/` com o catálogo extraído (zip já incluso em `Docs/courses.zip`).
- Chave da OpenAI ([platform.openai.com/api-keys](https://platform.openai.com/api-keys)).
- Para deploy como serviço: [nssm.exe](https://nssm.cc/download) no PATH.

---

## Setup — desenvolvimento local (Windows)

```cmd
REM 1. Extrair Docs\courses.zip em Docs\output\
REM    (clique direito -> Extrair tudo no proprio Docs\)

REM 2. Criar venv + dependencias
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

REM 3. Configurar a chave
copy .env.example .env
REM Abra .env no notepad e preencha OPENAI_API_KEY

REM 4. Indexar transcricoes (em uma janela cmd) - ~20 min, ~$0.17
indexar.bat

REM 5. Em OUTRA janela cmd: subir o servidor
iniciar.bat

REM Acesse http://localhost:8000
```

A indexação é idempotente — pode interromper com `Ctrl+C` e rodar de novo que retoma do ponto.

---

## Deploy — servidor Windows (Python + nssm como serviço)

Esse é o caminho **recomendado** para produção em qualquer Windows Server.

### Pré-requisitos no servidor
1. **Python 3.11+** instalado (marque "Add to PATH" no instalador).
2. **nssm.exe** colocado em `C:\Windows\System32` ou outro diretório do PATH.

### Passo a passo

```cmd
REM 1. Copiar o repo para o servidor (ex: C:\TutorCEFIS\)
REM    Extrair Docs\courses.zip em Docs\output\

REM 2. Criar venv + dependencias
cd C:\TutorCEFIS
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

REM 3. Configurar .env com OPENAI_API_KEY
copy .env.example .env
notepad .env

REM 4. Indexar UMA VEZ (gera data\cefis.db, ~260MB)
indexar.bat

REM 5. Instalar como servico (abra cmd como Administrador)
instalar-servico.bat
```

Pronto. O serviço `TutorCEFIS`:
- Sobe automaticamente no boot
- Reinicia sozinho se cair
- Log rotativo em `data\service-out.log` e `data\service-err.log`
- Porta `8000` (libere no firewall do servidor)

### Operações comuns

```cmd
nssm status TutorCEFIS          REM ver estado
nssm stop TutorCEFIS            REM parar
nssm start TutorCEFIS           REM iniciar
nssm restart TutorCEFIS         REM reiniciar
desinstalar-servico.bat         REM remover servico (como admin)
```

### Atualizando o código no servidor

```cmd
nssm stop TutorCEFIS
git pull                                 REM ou copiar arquivos
.venv\Scripts\pip install -r requirements.txt
nssm start TutorCEFIS
```

### Por trás de IIS / proxy reverso (opcional)

Se quiser servir em porta 80/443 com SSL gerenciado pelo IIS, configure IIS como reverse proxy para `http://localhost:8000` (URL Rewrite + Application Request Routing). O serviço continua igual.

---

## Plano B — Docker

Os arquivos `Dockerfile` e `docker-compose.yml` ficam no repo para quem prefere container (Linux, Fly.io, Railway etc.):

```bash
docker compose --profile index run --rm indexer   # indexa uma vez
docker compose up -d                              # sobe o serviço
```

Não é necessário em servidores Windows — use o caminho nssm acima.

---

## Estrutura

```
app/
  main.py          FastAPI — rotas /api/onboarding, /api/chat (SSE), /api/status
  db.py            SQLite + sqlite-vec — busca semântica + RAG
  llm.py           OpenAI — embeddings + chat streaming
  prompts.py       System prompts (diagnostico, plano, chat)
  static/
    index.html     SPA inteira (Tailwind + Alpine.js)

scripts/
  index_transcripts.py    Indexador VTT → SQLite + embeddings

Docs/
  courses.zip                catálogo da CEFIS (cursos + lições + VTTs)
  output/                    extração do zip (não vai pro git)
  specs/
    01-spec-logica.md        spec do projeto
    prototipo.html           protótipo visual standalone

data/
  cefis.db                   índice (~260MB depois de indexado)
  index_state.json           estado da última indexação
```

---

## Variáveis de ambiente (`.env`)

| Variável | Default | Descrição |
|---|---|---|
| `OPENAI_API_KEY` | — | **Obrigatória.** Chave da OpenAI. |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Modelo de embedding (1536 dims). |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Modelo de chat para diagnóstico/plano/chat. |
| `CEFIS_DATA_DIR` | `./Docs/output` | Caminho do catálogo extraído. |
| `CEFIS_DB_PATH` | `./data/cefis.db` | Caminho do SQLite com o índice. |
| `APP_HOST` | `0.0.0.0` | Bind do servidor. |
| `APP_PORT` | `8000` | Porta do servidor. |

---

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | SPA estática. |
| `GET` | `/api/status` | Estado do índice (cursos, chunks, embeddings, ready). |
| `POST` | `/api/onboarding` | Recebe perfil, devolve diagnóstico + plano. |
| `POST` | `/api/chat` | SSE streaming com RAG. Eventos: `sources`, `token`, `done`, `error`. |

---

## Notas do hackathon

- 476 cursos, 12.172 aulas, 7.447 com transcrição → **~34.000 chunks** vetoriais.
- O catálogo é local (não exige rede para o `/onboarding`, só para a IA).
- A integração com a API REST da CEFIS está prevista mas é opcional — o tutor funciona sem login.
- Spec lógica detalhada em [`Docs/specs/01-spec-logica.md`](Docs/specs/01-spec-logica.md).

---

## Licença

Projeto criado durante o **CEFIS Hackathon 2026**. Uso interno do hackathon.
