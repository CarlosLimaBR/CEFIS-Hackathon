# 🛠️ Setup local (Windows)

Como rodar o Tutor IA CEFIS na máquina local para desenvolvimento, teste ou demonstração offline.

> 🚀 Para deploy em servidor, consulte [DEPLOY.md](DEPLOY.md).

---

## 📋 Pré-requisitos

- **Python 3.11+** ([python.org/downloads](https://www.python.org/downloads/)) — marque "Add to PATH" no instalador.
- Pasta `Docs/output/` com o catálogo extraído (zip já vem em `Docs/courses.zip`).
- Chave da OpenAI ([platform.openai.com/api-keys](https://platform.openai.com/api-keys)).
- Espaço em disco: **~500 MB** (índice + dependências).

---

## 🚦 Passo a passo (~30 min, sendo ~25 min de indexação)

### 1. Clonar e extrair catálogo

```cmd
git clone https://github.com/CarlosLimaBR/CEFIS-Hackathon.git D:\Projects\CEFIS
cd D:\Projects\CEFIS\Docs
powershell -Command "Expand-Archive -Path courses.zip -DestinationPath output -Force"
```

Confira:
```cmd
dir Docs\output | findstr /R "DIR"
```
Deve listar ~476 pastas numéricas.

### 2. Venv + dependências

```cmd
cd D:\Projects\CEFIS
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configurar `.env`

```cmd
copy .env.example .env
notepad .env
```

Preencha `OPENAI_API_KEY=sk-proj-...` e salve.

### 4. Indexar transcrições (~20 min, ~$0.17)

Em um cmd:

```cmd
indexar.bat
```

A barra de progresso percorre 34.422 chunks. **Pode interromper com Ctrl+C** — ao rodar de novo, retoma do ponto.

Validação:
```cmd
type data\index_state.json
```
Deve mostrar `"embeddings": 34422`.

### 5. Subir o servidor

Em **outro cmd**:

```cmd
iniciar.bat
```

Acesse: **http://localhost:8000**

---

## 📁 Estrutura do projeto

```
app/
  main.py          FastAPI — rotas /api/onboarding, /api/chat (SSE), /api/quiz, /api/tts, /api/diag...
  db.py            SQLite + sqlite-vec — busca semântica e RAG
  llm.py           Wrappers OpenAI: embeddings, chat JSON, chat streaming, TTS
  cefis_api.py     Cliente HTTP das APIs CEFIS (login, /user/me, /performance, /tracks)
  prompts.py       System prompts (diagnóstico, plano, chat, quiz)
  static/
    index.html     SPA inteira (Tailwind via CDN + Alpine.js, zero build)
    *.svg          Logos oficiais CEFIS

scripts/
  index_transcripts.py    Indexador VTT → chunks → embeddings → SQLite
  test_endpoints.py       Suite E2E (9 testes)
  extract_pdf.py          Helper de leitura de PDFs

Docs/
  CEFIS_Hackathon_Briefing.pdf
  CEFIS_Hackathon_Docs_Dev_atualizado.pdf
  courses.zip              Catálogo da CEFIS (476 cursos + lições + VTTs)
  output/                  Extração do zip (gitignored)
  Logos/                   Logos oficiais
  specs/                   Spec lógica, protótipo, smoke test, roteiro de vídeo
  screenshots/             Capturas usadas no README

data/
  cefis.db                 Índice (~260 MB depois de indexado)
  index_state.json         Estado da última indexação

indexar.bat               Roda o indexador
iniciar.bat               Sobe o servidor local (uvicorn --reload)
atualizar.bat             Atualiza código do servidor (git pull + restart)
instalar-servico.bat      Registra como serviço Windows (nssm)
desinstalar-servico.bat   Remove o serviço

.env.example              Template — copie para .env e preencha
requirements.txt          Dependências Python
Dockerfile                Plano B: deploy via container
docker-compose.yml        Plano B: orquestração
web.config.recommended    web.config otimizado para IIS reverse proxy
```

---

## ⚙️ Variáveis de ambiente (`.env`)

| Variável | Default | Descrição |
|---|---|---|
| `OPENAI_API_KEY` | — | **Obrigatória**. Chave da OpenAI. |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Modelo de embedding (1536 dims). |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Modelo de chat (diagnóstico, plano, chat, quiz). |
| `OPENAI_TTS_MODEL` | `tts-1` | Modelo de áudio (botão 🔊). |
| `CEFIS_DATA_DIR` | `./Docs/output` | Caminho do catálogo extraído. |
| `CEFIS_DB_PATH` | `./data/cefis.db` | Caminho do SQLite com o índice. |
| `APP_HOST` | `0.0.0.0` | Bind do servidor. |
| `APP_PORT` | `8000` | Porta do servidor. |

---

## 🧪 Smoke test após instalar

Com o servidor rodando em http://localhost:8000:

```cmd
.venv\Scripts\python.exe scripts\test_endpoints.py
```

Esperado:
```
10/10 testes passaram
  OK  status
  OK  onboarding
  OK  chat
  OK  tts
  OK  quiz
  OK  courses_search
  OK  multi_fase
  OK  cefis_tracks
  OK  roleplay
  OK  resumos_com_ref
```

Se algo falhar, veja o terminal do `iniciar.bat` para a stack trace ou consulte `/api/diag` no browser:

```
http://localhost:8000/api/diag
```

---

## 🔗 Próximos passos

- 🏗️ Entender a aplicação: [ARQUITETURA.md](ARQUITETURA.md)
- 💾 Entender os dados: [DATABASE.md](DATABASE.md)
- 🚀 Deploy em servidor: [DEPLOY.md](DEPLOY.md)
