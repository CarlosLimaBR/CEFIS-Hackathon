# Tutor IA CEFIS

Tutor de aprendizado personalizado feito para o **Hackathon de Inovação em Aprendizado da CEFIS** (26/05/2026).

Onboarding curto, diagnóstico de lacunas, plano de estudos cronometrado usando o catálogo real, chat de dúvidas com RAG sobre as transcrições das aulas, quiz por aula, áudio em todo conteúdo gerado pela IA, trilha evolutiva multi-fase e histórico cumulativo.

🌐 **Acesse:** [https://tutor-cefis.duckdns.org](https://tutor-cefis.duckdns.org)

**Status:** ✅ 9/9 testes E2E (`scripts/test_endpoints.py`) + validação real no browser via Playwright headless. Deploy público em Windows Server com IIS + Let's Encrypt.

---

## 🏆 Em 1 minuto — o que mais pesa nessa entrega

> Diferenciais que **a maioria dos times não vai ter** e que cobrem os critérios mais valiosos do briefing (Funcionalidade 30pt + Integração CEFIS 25pt + Qualidade IA 20pt = 75% da nota).

1. **RAG profundo nas transcrições reais** — não busca por keyword na ementa. Indexei as **7.447 transcrições VTT** em **34.422 chunks vetoriais** (sqlite-vec, 1536 dims). O chat cita **curso + aula + segundo exato** onde aquela informação foi falada.
2. **Catálogo 100% local + 5 endpoints da API CEFIS conectados** — login, perfil, certificados, **trilhas oficiais** (`/tracks`) e **progresso por aula em tempo real** (`/courses/:id/lessons`). Sem rate-limit, sem latência de API no caminho crítico.
3. **Modelo de sessão recorrente "tenho X min agora"** — exatamente como o CEO da live descreveu ("15 min no ônibus, capitalize esse tempo"). Botão **Nova sessão** sempre visível, pergunta tempo atual, escolhe continuar mesmo objetivo ou trocar de tema. Histórico cumulativo garante zero repetição.
4. **Quiz dinâmico por aula** — 5 perguntas geradas em runtime da transcrição da aula específica, mix de dificuldade, feedback imediato, explicação justificada no conteúdo real.
5. **Áudio (TTS) em todo conteúdo gerado pela IA** — botão 🔊 no diagnóstico, resumos, chat e quiz. Atende "múltiplos formatos" + estilo de aprendizagem auditivo.

Bônus arquiteturais:
- **Toda saída da IA aponta de volta para uma aula real** — resumos têm "📎 Para se aprofundar:", chat cita fontes clicáveis, quiz tem "Assistir aula completa" no resultado.
- **"Instala em qualquer servidor"** — Python + venv + nssm como serviço Windows (sem Docker obrigatório), Dockerfile como plano B.
- **Zero build no frontend** — Tailwind + Alpine.js via CDN. Deploy = copiar arquivos.
- **Deploy real**: Windows Server + IIS + ARR + Let's Encrypt rodando em [tutor-cefis.duckdns.org](https://tutor-cefis.duckdns.org).

---

## 📸 Galeria de telas

<table>
  <tr>
    <td width="50%"><b>Onboarding em 3 passos</b><br/>Áreas inferidas do catálogo real (215 cursos de Fiscal & Tributário, 203 de Contábil, etc).<br/><br/><img src="Docs/screenshots/01-onboarding-passo1.png" alt="Onboarding passo 1"/></td>
    <td width="50%"><b>Objetivo livre</b><br/>O aluno escreve o que quer alcançar — base do diagnóstico da IA.<br/><br/><img src="Docs/screenshots/02-onboarding-passo2.png" alt="Onboarding passo 2"/></td>
  </tr>
  <tr>
    <td><b>Nível + tempo disponível</b><br/>Slider de 10min a 40h. A IA respeita o tempo declarado +10%.<br/><br/><img src="Docs/screenshots/03-onboarding-passo3.png" alt="Onboarding passo 3"/></td>
    <td><b>Seleção manual dos cursos</b><br/>O aluno vê os 12 cursos mais relevantes (busca semântica) e escolhe quais quer. Atalho para <b>trilhas oficiais</b> da CEFIS no topo (via API real).<br/><br/><img src="Docs/screenshots/04-selecao-cursos.png" alt="Seleção de cursos"/></td>
  </tr>
  <tr>
    <td colspan="2"><b>Plano + Chat com RAG</b><br/>Diagnóstico em prosa, plano com cards diferenciados (🎬 Aula CEFIS / 📝 Resumo IA), chat lateral cita curso + aula + segundo das transcrições reais. Áudio (🔊) em todo conteúdo gerado.<br/><br/><img src="Docs/screenshots/05-plano-chat.png" alt="Plano e chat"/></td>
  </tr>
  <tr>
    <td><b>Modal "Nova sessão"</b><br/>"Tenho X minutos agora" — gera próxima sessão respeitando o tempo atual, pulando o que já foi visto. Pode continuar mesmo objetivo ou trocar de tema.<br/><br/><img src="Docs/screenshots/06-modal-nova-sessao.png" alt="Modal Nova sessão"/></td>
    <td><b>Quiz por aula</b><br/>5 perguntas geradas da transcrição real da aula clicada. Mix de dificuldade, feedback imediato verde/vermelho, explicação justificada no conteúdo.<br/><br/><img src="Docs/screenshots/07-quiz.png" alt="Quiz"/></td>
  </tr>
  <tr>
    <td colspan="2"><b>Meu progresso (dashboard da trilha)</b><br/>Cards de stats agregados (aulas vistas, quizzes feitos com % médio, sessões/fases percorridas, tempo total estudado), plano atual com barra de progresso, distribuição por área de interesse, histórico das últimas sessões e quizzes recentes com nota colorida. Tudo lido do <code>localStorage</code> — sem chamada de backend.<br/><br/><img src="Docs/screenshots/08-meu-progresso.png" alt="Meu progresso"/></td>
  </tr>
</table>

---

## Como funciona

- **Onboarding (3 passos)** — perfil, objetivo livre, nível e tempo disponível.
- **Seleção manual de cursos** — antes do plano, o aluno vê os cursos candidatos rankeados por similaridade e escolhe quais quer.
- **Trilhas oficiais CEFIS** — atalho via integração com `GET /tracks` da API real: aluno pode adotar uma trilha curada pela CEFIS em vez de partir do zero.
- **Diagnóstico de lacunas** — IA cruza o objetivo com os cursos escolhidos e descreve o gap do aluno.
- **Continue de onde parou** — quando logado, o sistema lê o `progress` real das aulas via API CEFIS e o tutor sugere retomar onde o aluno estava.
- **Plano de estudos** — sequência ordenada de aulas reais + resumos da IA, respeitando o tempo declarado.
- **Chat com RAG** — perguntas livres respondidas com base no texto das aulas, citando curso/aula/segundo.
- **Quiz por aula** — botão "Testar" em cada aula gera 5 perguntas múltipla escolha a partir da transcrição real.
- **Áudio em todo conteúdo gerado** — botão 🔊 no diagnóstico, resumos, chat e quiz.
- **Trilha evolutiva multi-fase** — ao concluir o plano, botão "Próxima fase" gera o próximo nível excluindo o que já foi visto.
- **Histórico local cumulativo** — aulas concluídas, quizzes feitos e cursos consumidos ficam no `localStorage` e influenciam os próximos planos automaticamente.
- **Dashboard "Meu progresso"** — botão 📊 no header mostra stats agregados, plano atual com %, sessões anteriores, quizzes recentes e distribuição por área.

Stack: **Python + FastAPI + SQLite + sqlite-vec + OpenAI**. Frontend HTML estático com Tailwind via CDN e Alpine.js (zero build).

---

## Atendimento aos requisitos do hackathon

### Entrega mínima obrigatória (briefing §4.1)

| Requisito | Como entregamos | Onde no código | Status |
|---|---|---|---|
| **Onboarding** — coleta perfil, objetivos, experiência e nível | Wizard de 3 passos com nome, áreas (7), objetivo livre, nível (3 níveis) e tempo (10min–40h) | [app/static/index.html](app/static/index.html) (telas 1–3) | ✅ |
| **Diagnóstico de lacunas** — identifica o que falta para o objetivo | Prompt `DIAGNOSIS_SYSTEM` cruza objetivo + nível com top-N cursos por similaridade vetorial. Saída JSON com `diagnosis` + lista de tópicos | [app/prompts.py:1](app/prompts.py:1) + [app/main.py:124](app/main.py:124) | ✅ |
| **Plano de estudos** — combina catálogo CEFIS + IA, respeita tempo | Prompt `PLAN_SYSTEM` monta sequência de itens `aula` (real) ou `resumo` (IA), regra de duração ≤ tempo +10%. Cada item linka para `cefis.com.br/curso/{slug}/{id}` | [app/prompts.py:39](app/prompts.py:39) + [app/main.py:170](app/main.py:170) | ✅ |

### Diferenciais valorizados (briefing §4.2)

| Diferencial | Como entregamos | Status |
|---|---|---|
| **Geração de conteúdo original** | Resumos da IA inseridos no plano quando o catálogo não cobre; quiz com 5 perguntas geradas da transcrição real (4 alternativas + gabarito + explicação) | ✅ |
| **Interação de dúvidas com material real** | Chat com SSE streaming. RAG sobre **34.422 chunks** vetoriais das transcrições; cita **curso, aula e segundo** de origem | ✅ |
| **Acompanhamento contínuo** | Histórico local persistente (aulas, quizzes, cursos) + checkbox "concluído" + quiz por aula + **trilha evolutiva multi-fase** que avança o aluno sem repetir o que já viu | ✅ |
| **Interface bem projetada** | Wizard com progresso animado, branding CEFIS (logos oficiais), responsivo, perfil persiste em `localStorage` (sobrevive refresh) | ✅ |
| **Múltiplos formatos** | Texto + chat conversacional + quiz interativo + **áudio TTS** (botão 🔊 em diagnóstico, resumos, chat, quiz) | ✅ |
| **Adaptação ao estilo de aprendizagem** (visual/auditivo/cinestésico) | Áudio cobre o estilo **auditivo**; texto + diagramas cobrem o **visual**; quiz interativo cobre o **cinestésico** (engajamento ativo). Sem auto-detecção do estilo dominante. | ⚠️ parcial |

### Critérios de avaliação (briefing §5)

| Critério | Peso | Como cobrimos |
|---|---|---|
| **Funcionalidade** | 30 pts | **9/9 testes E2E** passando ([scripts/test_endpoints.py](scripts/test_endpoints.py)) + validação real via Playwright. Fluxo completo: onboarding → seleção → plano → chat (SSE) → quiz → TTS → trilhas oficiais → multi-fase |
| **Integração com a CEFIS** | 25 pts | Catálogo CEFIS **inteiro** indexado (476 cursos, 12.172 aulas). URLs apontam para `cefis.com.br/curso/{slug}/{id}` reais. **5 endpoints da API CEFIS conectados**: login, /user/me, /performance/certificates, **/tracks (trilhas oficiais)** e **/courses/:id/lessons com progresso real** |
| **Qualidade da IA** | 20 pts | RAG profundo: top-K chunks por similaridade sqlite-vec, prompts com regras anti-alucinação, citação obrigatória de fonte, resposta em streaming |
| **Inovação** | 15 pts | Quiz gerado por aula a partir da transcrição real (não pergunta genérica); citação por **segundo** da aula no chat; remoção de cursos já certificados; spec lógica documentada antes do código |
| **Experiência do usuário** | 10 pts | Branding CEFIS, animações suaves, persistência de progresso, mensagens de erro claras, modal de quiz com feedback imediato visual (verde/vermelho) |

---

## Diferenciais do projeto (além do briefing)

1. **🏆 RAG profundo nas transcrições reais, com citação por segundo**
   34.422 chunks vetoriais de 7.447 transcrições VTT. Quando o chat responde, traz o segundo exato onde aquele tópico é discutido na aula — clicável, abre o curso na CEFIS.

2. **🏆 Catálogo 100% local indexado**
   Sem rate limit da API CEFIS, sem latência de rede, funciona offline depois de indexado. Busca semântica instantânea em todos os 476 cursos.

3. **🏆 Quiz dinâmico por aula**
   Gerado em runtime a partir da transcrição da aula específica — 5 perguntas com mix de dificuldade (lembrar/entender/aplicar), feedback imediato e explicação justificada no conteúdo real.

4. **🏆 Login CEFIS opcional com análise retroativa**
   Botão "Já tem conta CEFIS?" autentica via API oficial. Quando logado, o sistema puxa certificados conquistados e **remove esses cursos** dos candidatos do plano — atende o "ver se a pessoa já assistiu" mencionado na live.

5. **🏆 "Instala em qualquer servidor" sem Docker obrigatório**
   Stack pura Python + venv. Script `instalar-servico.bat` registra como serviço Windows via nssm em 4 passos. Docker disponível como Plano B para Linux/cloud.

6. **🏆 Zero build no frontend**
   HTML + Alpine.js + Tailwind via CDN. Deploy = copiar arquivos. Sem npm, sem webpack, sem CI complicada.

7. **🏆 URLs reais da plataforma**
   Função `slugify()` gera o slug correto da CEFIS (`/curso/{slug}/{id}`) com normalização de acentos. Clicar em qualquer aula do plano ou em qualquer fonte do chat abre o curso de verdade na cefis.com.br.

8. **🏆 Perfil persistente sem banco**
   Tudo que o aluno preenche fica em `localStorage` + cookie httpOnly (CEFIS key). Refresh, fechar e abrir o browser, manter sessão — nada se perde.

9. **🏆 Spec lógica + protótipo antes do código**
   [Docs/specs/01-spec-logica.md](Docs/specs/01-spec-logica.md) com escopo, mapeamento de dados, diagramas Mermaid e checklist. [Docs/specs/prototipo.html](Docs/specs/prototipo.html) standalone para validação visual.

10. **🏆 Testes E2E automatizados**
    [scripts/test_endpoints.py](scripts/test_endpoints.py) valida status, onboarding, chat SSE, TTS, quiz, busca de cursos, trilha multi-fase, trilhas oficiais CEFIS e referências em resumos. **9/9 passando** no momento da entrega.

11. **🏆 Áudio em todo conteúdo gerado pela IA**
    Botão 🔊 ao lado do diagnóstico, dos resumos do plano, das respostas do chat e das explicações do quiz. MP3 streaming via OpenAI TTS (`tts-1`), toggle play/pausa, cache por sessão.

12. **🏆 Toda saída da IA aponta para uma aula real**
    Resumo gerado pela IA? Mostra **"📎 Para se aprofundar:"** com 1-2 aulas relacionadas semanticamente (buscadas via embedding do título do resumo). Resposta do chat? Cita curso + aula + segundo. Quiz? Resultado final tem botão "Assistir a aula completa". O aluno **nunca** fica sem caminho para o material original.

13. **🏆 Trilha evolutiva multi-fase**
    Quando o aluno conclui todos os itens de um plano, surge o botão **"Próxima fase ⤴"**. A próxima fase usa o mesmo objetivo, exclui automaticamente as aulas já vistas e instrui a IA a aprofundar (não repetir fundamentos). Sem limite de fases — vira uma trilha personalizada que evolui com o aluno.

14. **🏆 Seleção manual dos cursos antes do plano**
    Após o onboarding, o aluno vê os 12 cursos mais relevantes ao objetivo (busca semântica) e marca quais quer. O plano é montado **só com os cursos escolhidos**, dando controle real ao aluno em vez de a IA decidir sozinha. Cursos já certificados (via login CEFIS) e cursos já concluídos no histórico local são automaticamente removidos.

15. **🏆 Histórico local cumulativo**
    `localStorage` guarda toda aula concluída, todo quiz feito (com nota), todo curso terminado e os planos anteriores. Esse histórico é enviado em **cada novo onboarding** como `exclude_lesson_ids` e `exclude_course_ids`, garantindo que o tutor nunca recomende algo que o aluno já viu — em qualquer fase, em qualquer sessão futura.

16. **🏆 Integração com trilhas oficiais da CEFIS**
    Endpoint `GET /api/cefis-tracks` consome a API real `/tracks` e mostra ao aluno **trilhas curadas pela própria CEFIS** como atalho. Selecionar uma trilha popula os `course_ids` do plano com a curadoria oficial. **20 trilhas reais** carregadas em ~400ms.

17. **🏆 "Continue de onde parou" com progresso real**
    Quando o aluno está logado, o backend chama `/courses/:id/lessons` em paralelo (asyncio.gather) para os 3 cursos mais relevantes ao objetivo, lê o `progress.percentage` real e identifica **aulas em andamento** (entre 5% e 90%). Essa informação vai para o prompt do diagnóstico, que recomenda explicitamente retomar de onde parou.

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

> 💡 **Guia rápido pronto:** [DEPLOY.md](DEPLOY.md) tem o checklist de 10 passos especificamente para servidor com IIS reverse proxy (~40 min, incluindo indexação).

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
