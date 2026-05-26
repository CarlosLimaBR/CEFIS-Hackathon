# Próximas funcionalidades

Roadmap pós-hackathon, organizado por **prazo + impacto**. Pensa o tutor como produto vivo, não só MVP.

> Estado atual: backend FastAPI (20 rotas), 10/10 testes E2E, deploy em [tutor-cefis.duckdns.org](https://tutor-cefis.duckdns.org). Veja [README.md](README.md) e [ARQUITETURA.md](ARQUITETURA.md).

---

## ✅ Já implementado (até 26/05/2026)

Snapshot do que ficou pronto no hackathon e foi entregue à banca:

### Núcleo
- **Onboarding** em 3 passos + seleção manual de cursos candidatos
- **Diagnóstico contextual** ("Mensagem do tutor") que reconhece histórico, cita conceitos dominados e apresenta a sessão atual em 2-3 frases
- **Plano de estudos** com cards diferenciados (Aula CEFIS / Resumo IA / Quiz)
- **Resumos com markdown rico** (headings, listas, negrito, diagramas Mermaid)
- **Welcome screen** com retomada inteligente para quem volta
- **Modal de conclusão de sessão** com opções "Praticar" / "Nova sessão"
- **Loading dinâmico** com 12 etapas em pool + 12 dicas rotativas das features

### Interação
- **Chat com RAG profundo** em 34.422 chunks vetoriais, citando curso/aula/segundo
- **Áudio TTS** em todo conteúdo gerado pela IA (botão 🔊)
- **Autoplay** da mensagem do tutor ao iniciar sessão (efeito "tutor te recebe falando")
- **Chat por voz** hands-free (Web Speech API + auto-TTS na resposta)
- **Roleplay** ("Pratique com o tutor"): IA interpreta personagem, feedback estruturado com nota e aulas recomendadas
- **Voz no roleplay** com TTS automático do personagem
- **Quiz dinâmico** gerado da transcrição real da aula clicada

### Gamificação profissional
- **Trajetória de Mestria**: conceitos dominados = aula concluída + quiz ≥80%
- **Toast discreto** ao dominar novo conceito (sem confetti, sem dark patterns)
- **Insights automáticos**: sessões esta semana vs média, melhor período do dia (manhã/tarde/noite), taxa de retenção, conceitos novos
- **Sem streak agressivo, sem ranking social** — design para profissionais adultos

### Personalização e trilha
- **Histórico cumulativo** em localStorage (aulas, quizzes com nota, cursos, planos, conceitos)
- **Nova sessão recorrente** "tenho X minutos agora" — continuar mesmo objetivo ou trocar de tema
- **Trilha multi-fase**: cada sessão concluída libera próxima fase, excluindo automaticamente o que já foi visto
- **Trilhas oficiais CEFIS** via API real (`/tracks`) como atalho ao objetivo livre
- **Resumos linkam para aulas reais** ("Para se aprofundar:")

### Integração CEFIS (5 endpoints)
- `POST /api/v1/login` + `GET /api/v1/user/me`
- `GET /performance/certificates` (remove cursos já certificados do plano)
- `GET /tracks` + `GET /tracks/:id` (trilhas oficiais)
- `GET /courses/:id/lessons` com progress real ("continue de onde parou")

### UX / produto
- **Modo escuro** com toggle persistente
- **Logos CEFIS oficiais** em todas as telas
- **Slug correto** nas URLs (`/curso/{slug}/{id}`)
- **Perfil persistente** em localStorage (sobrevive refresh)
- **Dashboard "Meu Progresso"** com cards de stats + trajetória + insights

### Operacional
- **Deploy público** Windows Server + IIS + nssm + Let's Encrypt
- **Scripts .bat** para indexar, iniciar, instalar serviço, atualizar
- **10/10 testes E2E** automatizados ([scripts/test_endpoints.py](scripts/test_endpoints.py))
- **Validação Playwright** real no browser (chat, modal, dark mode)

---

## ⚡ Quick wins (1-2 semanas cada)

Coisas que **ainda cabem** na arquitetura atual sem refatorar.

| Feature | Por quê | Esforço |
|---|---|---|
| **Spaced repetition no quiz** (Anki-style) | Aluno revisa o que errou há 1/3/7/14 dias. Multiplica retenção sem custo extra de LLM | Médio |
| **Ritmo voluntário** (Fase 2 da gamificação) | Aluno define ritmo desejado (1-2x/sem, 2-3x/sem...) e vê comparativo sem pressão. Modo férias incluso. | Baixo (1h) |
| **Marcas com certificado PDF** (Fase 4 da gamificação) | "Você concluiu IFRS 16 — baixe certificado + compartilhe no LinkedIn". `jspdf` via CDN | Médio (2h) |
| **Marcar aula concluída pelo chat** | "Já assisti essa aula" → tutor entende e marca via function calling do LLM | Baixo |
| **Anotações por aula** | Textarea livre por `lesson_id` persistida em localStorage. "Meu caderno" agregado | Baixo |
| **Compartilhar plano por link** | URL com payload do plano em base64. "Olha o que estou estudando" | Baixo |
| **PWA installable** | `manifest.json` + service worker leve. Vira "app" no celular | Baixo |
| **Resumo em PDF para download** | Plano + diagnóstico + resumos da IA em um PDF | Médio |
| **Atalhos de teclado** | J/K navega plano, Enter abre, `?` ajuda, `/` foca chat | Trivial |

---

## 🎯 Médio prazo (1-3 meses)

### Personalização adaptativa real

- **Detecção do estilo de aprendizagem por comportamento**: se o aluno consome mais áudio que texto, prioriza TTS. Se faz muitos quizzes, prioriza prática. Sem auto-declaração — observa.
- **Ajuste de dificuldade do quiz** com base no histórico de acertos por tópico
- **Recomendação colaborativa**: "alunos com objetivo parecido também fizeram X"
- **Memória persistente do tutor** (mem0 / Letta-style): lembra "você me disse semana passada que tem dificuldade com IFRS"

### Conteúdo gerado expandido

- **Flashcards gerados** com revisão espaçada (cards extraídos das transcrições)
- **Podcast diário personalizado** — 5 min de áudio resumindo o que o aluno deveria saber hoje
- **Avaliação dissertativa** — aluno responde por extenso, IA dá nota e feedback (vs múltipla escolha atual)
- **Modo "explique como se..."** — slider iniciante↔expert ajusta complexidade da resposta no chat

### Integração CEFIS aprofundada

- **Sincronizar progresso bidirecional** — marcar aula no tutor reflete na conta CEFIS
- **Inscrição automática** em curso pelo tutor (botão "matricular")
- **Trilhas próprias do aluno** — salvar combinação personalizada como trilha reusável
- **Emissão automática de certificado** quando aluno completa critério
- **Importar planos de RH** — empresa cria trilha obrigatória, aluno acessa via login corporativo

---

## 🚀 Longo prazo (3-12 meses)

### IA agente

- **Agente proativo**: detecta que o aluno está parado há N dias e oferece sessão curta
- **Tutor multi-agente**: diagnosticador + explicador (RAG) + examinador (quiz) + motivador. Orchestrator escolhe quem fala
- **Geração de conteúdo quando o catálogo não cobre**: tutor cria uma "aula CEFIS-style" totalmente nova com vídeo TTS + slides
- **Análise dissertativa profunda** com rubrica configurável pelo professor

### Comunidade

- **Q&A público da comunidade** com voting (StackOverflow-style por curso)
- **Estudar em grupo** — mesma trilha, mesma fase, sincronizada
- **Mentoria peer-to-peer** matched por nível complementar

### Operacional / negócio

- **Multi-tenant B2B**: empresas com sub-domínio próprio, white-label, dashboard de gestor
- **Marketplace de trilhas** criadas por professores top
- **API pública**: devs constroem em cima (Slack bot, integração LMS, etc)
- **Modelo freemium** com limites mensais
- **Compliance educacional**: SCORM, integração com Moodle/Canvas

### Infra

- **Postgres + pgvector** em vez de SQLite (multi-instância, alta disponibilidade)
- **Cache Redis** de respostas frequentes (mesma pergunta de N alunos → 1 chamada à OpenAI)
- **Observabilidade**: Sentry + OpenTelemetry, dashboards de uso
- **A/B testing de prompts** — qual versão do `DIAGNOSIS_SYSTEM` engaja mais?
- **Fine-tuning próprio** de modelo pequeno (Qwen 7B) no corpus CEFIS para reduzir custo OpenAI

---

## 📊 Acessibilidade & UX

- Internacionalização (PT-BR / EN / ES)
- WCAG AA: leitor de tela, alto contraste, navegação por teclado completa
- Modo offline parcial: download de aulas + transcrições para o celular
- Tema customizável (escuro, sépia, alto contraste)

---

## 🔒 Segurança & privacidade

- Rate limit por IP/usuário
- Sanitização de input nos prompts (proteção contra prompt injection)
- Cifra de cookies de sessão CEFIS no servidor
- LGPD: política de privacidade, opt-in para uso de dados de progresso para recomendação colaborativa
- Auditoria de chamadas à API CEFIS (timestamps + IPs)

---

## 💡 Ideias mais ousadas

- **"Pergunte ao professor da aula"**: clonar voz e estilo do professor (com permissão) e responder no chat como se fosse ele
- **Simulação de prova CRC** com timer, questões oficiais e relatório de prontidão
- **Tutoria peer guiada por IA**: o tutor identifica dois alunos no mesmo tema e sugere conversa
- **Recomendação preditiva**: "Em 2 semanas vai sair uma nova legislação X — comece a estudar essa aula"
- **Modo apresentação**: aluno termina trilha → IA gera slides para apresentar pra equipe na empresa

---

## Filosofia de design (resumo do que aprendemos)

- **Mestria mensurável** > XP abstrato
- **Auto-comparação** > ranking social
- **Insights úteis** > notificações de pressão
- **Linguagem profissional** > gamificação infantil
- **Recompensa funcional** (desbloqueio de conteúdo avançado) > cosmética
- **Tutor que reconhece o aluno** > diagnóstico genérico

Esses princípios guiam as próximas features.

---

## Como contribuir

PRs bem-vindos. Antes de começar uma feature grande:

1. Abra uma issue descrevendo o problema/oportunidade
2. Mantenha o padrão atual: zero build no frontend, prompts em `app/prompts.py`, schema em `db.py`
3. Adicione teste E2E em `scripts/test_endpoints.py`
4. Rode `python scripts/test_endpoints.py` antes de PR (10/10 deve continuar passando)
