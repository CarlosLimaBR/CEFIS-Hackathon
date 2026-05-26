# Tutor IA CEFIS

Tutor de aprendizado personalizado feito para o **Hackathon de Inovação em Aprendizado da CEFIS** (26/05/2026).

Onboarding curto, diagnóstico de lacunas, plano de estudos cronometrado usando o catálogo real, chat de dúvidas com RAG sobre as transcrições das aulas, quiz por aula, áudio em todo conteúdo gerado pela IA, trilha evolutiva multi-fase, histórico cumulativo e dashboard de progresso.

🌐 **Acesse:** [https://tutor-cefis.duckdns.org](https://tutor-cefis.duckdns.org)

**Status:** ✅ 9/9 testes E2E (`scripts/test_endpoints.py`) + validação real no browser via Playwright headless. Deploy público em Windows Server com IIS + Let's Encrypt.

---

## 📚 Documentação

| Documento | O que tem |
|---|---|
| [**SETUP.md**](SETUP.md) | Como instalar e rodar localmente (Windows) |
| [**DEPLOY.md**](DEPLOY.md) | Como deployar em servidor Windows com IIS + nssm |
| [**ARQUITETURA.md**](ARQUITETURA.md) | Stack, fluxos, diagramas, decisões de design |
| [**DATABASE.md**](DATABASE.md) | Schema do SQLite + sqlite-vec, queries-chave, estado da indexação |
| [**PROXIMAS_FUNCIONALIDADES.md**](PROXIMAS_FUNCIONALIDADES.md) | Roadmap pós-hackathon (quick wins → longo prazo) |
| [Docs/specs/01-spec-logica.md](Docs/specs/01-spec-logica.md) | Spec lógica original (escopo + mapeamento de dados) |
| [Docs/specs/video-demo-roteiro.md](Docs/specs/video-demo-roteiro.md) | Roteiro do vídeo de apresentação |

---

## 🏆 Em 1 minuto — o que mais pesa nessa entrega

> Diferenciais que **a maioria dos times não vai ter** e que cobrem os critérios mais valiosos do briefing (Funcionalidade 30pt + Integração CEFIS 25pt + Qualidade IA 20pt = 75% da nota).

1. **RAG profundo nas transcrições reais** — não busca por keyword na ementa. Indexei as **7.447 transcrições VTT** em **34.422 chunks vetoriais** (sqlite-vec, 1536 dims). O chat cita **curso + aula + segundo exato** onde aquela informação foi falada.
2. **Catálogo 100% local + 5 endpoints da API CEFIS conectados** — login, perfil, certificados, **trilhas oficiais** (`/tracks`) e **progresso por aula em tempo real** (`/courses/:id/lessons`). Sem rate-limit, sem latência de API no caminho crítico.
3. **Modelo de sessão recorrente "tenho X min agora"** — exatamente como o CEO da live descreveu ("15 min no ônibus, capitalize esse tempo"). Botão **Nova sessão** sempre visível, pergunta tempo atual, escolhe continuar mesmo objetivo ou trocar de tema. Histórico cumulativo garante zero repetição.
4. **Quiz dinâmico por aula** — 5 perguntas geradas em runtime da transcrição da aula específica, mix de dificuldade, feedback imediato, explicação justificada no conteúdo real.
5. **Áudio (TTS) em todo conteúdo gerado pela IA** — botão 🔊 no diagnóstico, resumos, chat e quiz. Atende "múltiplos formatos" + estilo de aprendizagem auditivo.
6. **Dashboard "Meu progresso"** — cards de stats, plano atual com %, sessões anteriores, quizzes recentes, distribuição por área. Tudo do `localStorage`, atualiza sozinho.

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
    <td colspan="2"><b>Meu progresso (dashboard da trilha)</b><br/>Cards de stats agregados, plano atual com barra, distribuição por área, histórico das últimas sessões e quizzes recentes com nota colorida. Tudo lido do <code>localStorage</code> — sem chamada de backend.<br/><br/><img src="Docs/screenshots/08-meu-progresso.png" alt="Meu progresso"/></td>
  </tr>
</table>

---

## Atendimento aos requisitos do hackathon

### Entrega mínima obrigatória (briefing §4.1)

| Requisito | Como entregamos | Status |
|---|---|---|
| **Onboarding** — coleta perfil, objetivos, experiência e nível | Wizard de 3 passos com nome, áreas (7), objetivo livre, nível e tempo (10min–40h) | ✅ |
| **Diagnóstico de lacunas** — identifica o que falta para o objetivo | Prompt `DIAGNOSIS_SYSTEM` cruza objetivo + nível com top-N cursos por similaridade vetorial | ✅ |
| **Plano de estudos** — combina catálogo CEFIS + IA, respeita tempo | Prompt `PLAN_SYSTEM` monta sequência de itens `aula` (real) ou `resumo` (IA), regra de duração ≤ tempo +10% | ✅ |

### Diferenciais valorizados (briefing §4.2)

| Diferencial | Status |
|---|---|
| Geração de conteúdo original (resumos + quiz da IA) | ✅ |
| Interação de dúvidas com material real (chat com RAG) | ✅ |
| Acompanhamento contínuo (histórico + trilha multi-fase + dashboard) | ✅ |
| Interface bem projetada (branding CEFIS, persistência) | ✅ |
| Múltiplos formatos (texto + chat + quiz + áudio TTS) | ✅ |
| Adaptação ao estilo de aprendizagem | ⚠️ parcial (auditivo via TTS, visual via texto/diagramas, cinestésico via quiz interativo — sem auto-detecção) |

### Critérios de avaliação (briefing §5)

| Critério | Peso | Cobertura |
|---|---|---|
| **Funcionalidade** | 30 pts | **9/9 testes E2E** + validação Playwright real |
| **Integração com a CEFIS** | 25 pts | 476 cursos indexados + **5 endpoints da API CEFIS conectados** |
| **Qualidade da IA** | 20 pts | RAG profundo, anti-alucinação, streaming, citação obrigatória de fonte |
| **Inovação** | 15 pts | Quiz da transcrição real + citação por segundo + sessão recorrente + retomar de onde parou |
| **Experiência do usuário** | 10 pts | Branding, animações, persistência, mensagens claras, feedback visual |

---

## Stack

**Backend:** Python 3.11 + FastAPI + SQLite + sqlite-vec + OpenAI (gpt-4o-mini, text-embedding-3-small, tts-1).
**Frontend:** HTML + Tailwind CDN + Alpine.js. Zero build.
**Deploy:** Windows Server + IIS (URL Rewrite + ARR) + nssm + Let's Encrypt.

Detalhes em [ARQUITETURA.md](ARQUITETURA.md).

---

## Quick start

```cmd
git clone https://github.com/CarlosLimaBR/CEFIS-Hackathon.git
cd CEFIS-Hackathon
powershell -Command "Expand-Archive -Path Docs\courses.zip -DestinationPath Docs\output -Force"
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
notepad .env                       REM preencha OPENAI_API_KEY
indexar.bat                        REM ~25 min, ~$0.17
iniciar.bat                        REM em outro cmd
```

Acesse http://localhost:8000.

Passo a passo completo: [SETUP.md](SETUP.md). Deploy: [DEPLOY.md](DEPLOY.md).

---

## Licença

Projeto criado durante o **CEFIS Hackathon 2026**. Uso interno do hackathon.
