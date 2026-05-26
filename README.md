# Tutor IA CEFIS

Tutor de aprendizado personalizado feito para o **Hackathon de Inovação em Aprendizado da CEFIS** (26/05/2026).

Onboarding curto, mensagem contextual do tutor (com áudio automático), plano cronometrado usando o catálogo real, chat com RAG sobre as transcrições, quiz por aula, áudio em todo conteúdo gerado, trilha evolutiva multi-fase, dashboard com **Trajetória de Mestria** + insights automáticos, welcome screen com retomada inteligente, loading dinâmico com dicas das features, **chat por voz hands-free** e **roleplay aplicado** ("pratique apresentar PDCA para o seu CFO cético").

🌐 **Acesse:** [https://tutor-cefis.duckdns.org](https://tutor-cefis.duckdns.org)

**Status:** ✅ 10/10 testes E2E (`scripts/test_endpoints.py`) + validação real no browser via Playwright headless. 20 rotas backend. Deploy público em Windows Server com IIS + Let's Encrypt.

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

1. **🎭 "Pratique com o tutor" (roleplay aplicado)** — único. Aluno escolhe cenário real (apresentar pro CFO, defender em auditoria, negociar com cliente), tutor **interpreta o personagem** e faz perguntas duras. No fim, **feedback estruturado** com nota, pontos fortes/melhoria e aulas CEFIS linkadas. Aprendizado ativo (Feynman) vs passivo. **Funciona por voz**.
2. **🎤 Chat por voz hands-free** — Web Speech API + TTS. Fala a pergunta → tutor responde em voz alta. Atende "15 min no ônibus" da live literalmente.
3. **💬 Mensagem do tutor contextual** — em 2-3 frases reconhece nominalmente o que você já dominou, explica o que esta sessão entrega e fecha com motivação profissional. **Toca em áudio automaticamente** quando o plano carrega — você é recebido pelo tutor falando.
4. **🎓 Trajetória de Mestria** — conceitos dominados = aula concluída **+** quiz com ≥80%. Métrica de retenção real, não "abriu o app". Insights automáticos ("Você acerta 95% à noite", "Sua retenção em IFRS é 80%"). **Sem streak, sem ranking social** — gamificação profissional pra adultos.
5. **🧠 RAG profundo nas transcrições reais** — 7.447 VTTs em **34.422 chunks vetoriais** (sqlite-vec). Chat cita **curso + aula + segundo exato**.
6. **🔗 Catálogo 100% local + 5 endpoints da API CEFIS** — login, perfil, certificados, **trilhas oficiais** e **progresso por aula em tempo real**.
7. **➕ Sessão recorrente "tenho X min agora"** — Nova sessão sempre visível, pergunta tempo atual, continua mesmo objetivo ou troca de tema. Zero repetição via histórico cumulativo.
8. **👋 Welcome screen** — quem volta é recebido por nome com botão "▶ Continuar sessão atual". "Tutor que te conhece" em 1 segundo.
9. **🎬 Loading dinâmico** — etapas sorteadas a cada geração + **12 dicas rotativas** apresentando as features. Nunca se repete.
10. **📝 Resumos com markdown rico + diagramas Mermaid** — quando o tema é sequencial (PDCA, DMAIC), o resumo vira fluxograma visual.
11. **❓ Quiz dinâmico por aula** + **🔊 áudio TTS em todo conteúdo gerado**.
12. **📊 Dashboard "Meu progresso"** com cards, distribuição por área e histórico de sessões.
13. **🌙 Modo escuro** com toggle persistente.

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
  <tr>
    <td colspan="2"><b>👋 Welcome screen — retomada inteligente</b><br/>Quando o aluno volta no app, em vez de cair no onboarding cai aqui: nome próprio, badge de fase, último plano, progresso agregado e botão grande "▶ Continuar sessão atual". Materializa "o tutor que te conhece" em 1 segundo de demo.<br/><br/><img src="Docs/screenshots/09-welcome.png" alt="Welcome screen"/></td>
  </tr>
  <tr>
    <td><b>🎭 Pratique — escolha do cenário</b><br/>4 cenários reais prontos (CFO cético, auditoria, cliente exigente, treinamento interno) + opção de descrever cenário próprio. Aluno escolhe e a IA assume o personagem.<br/><br/><img src="Docs/screenshots/10-roleplay-cenarios.png" alt="Roleplay cenários"/></td>
    <td><b>🎭 Simulação em andamento</b><br/>IA fala como o personagem (CFO cético no exemplo), faz objeções concretas, mantém pressão. Aluno responde por texto ou voz. Botão "🎯 Encerrar e ver feedback" libera após 2 trocas.<br/><br/><img src="Docs/screenshots/11-roleplay-simulacao.png" alt="Roleplay simulação"/></td>
  </tr>
  <tr>
    <td colspan="2"><b>🎭 Feedback estruturado do roleplay</b><br/>Nota 0-10 com cor por faixa, resumo geral em 1 frase, pontos fortes + pontos a melhorar, e <b>3 aulas reais do catálogo CEFIS</b> linkadas para o aluno aprofundar onde ficou fraco. Aprendizado ativo + retorno para o material original.<br/><br/><img src="Docs/screenshots/12-roleplay-feedback.png" alt="Roleplay feedback"/></td>
  </tr>
  <tr>
    <td colspan="2"><b>🌙 Modo escuro + 🎤 microfone</b><br/>Toggle sol/lua no header, persiste em localStorage. Botão de microfone ao lado do input do chat: Web Speech API capta voz, envia automático e a resposta toca em áudio (TTS). Hands-free total.<br/><br/><img src="Docs/screenshots/13-dark-mode.png" alt="Modo escuro com microfone"/></td>
  </tr>
  <tr>
    <td colspan="2"><b>🎓 Trajetória de Mestria + Insights</b><br/>Gamificação profissional para adultos (sem streak agressivo, sem ranking social). <b>Conceitos dominados</b> = aula concluída <b>+</b> quiz com ≥80%. Mostra retenção real (não "abriu o app"), distribuição por área e <b>insights automáticos</b> ("Você acerta 95% à noite", "+275% vs sua média"). Toast discreto ao dominar novo conceito.<br/><br/><img src="Docs/screenshots/14-mestria-insights.png" alt="Trajetória de Mestria"/></td>
  </tr>
  <tr>
    <td colspan="2"><b>🎬 Loading dinâmico com dicas rotativas</b><br/>Cada geração de plano sorteia 4 etapas de um pool de 12 (sempre diferente), incluindo etapas <b>contextuais</b> ("Considerando o que você já dominou" só se há conceitos dominados). Embaixo, card com 12 dicas das funcionalidades em rotação — o aluno descobre o sistema enquanto espera.<br/><br/><img src="Docs/screenshots/15-loading-dinamico.png" alt="Loading dinâmico"/></td>
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
| **Funcionalidade** | 30 pts | **10/10 testes E2E** + validação Playwright real |
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
