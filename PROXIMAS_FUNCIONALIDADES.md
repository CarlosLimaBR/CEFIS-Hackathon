# Próximas funcionalidades

Roadmap pós-hackathon, organizado por **prazo + impacto**. Pensa o tutor como produto vivo, não só MVP.

> Estado atual: backend FastAPI (18 rotas), 9/9 testes E2E, deploy em [tutor-cefis.duckdns.org](https://tutor-cefis.duckdns.org). Veja [README.md](README.md) e [ARQUITETURA.md](ARQUITETURA.md).

---

## ⚡ Quick wins (1-2 semanas cada)

Encaixam direto na arquitetura atual, sem refatorar nada.

| Feature | Por quê | Esforço |
|---|---|---|
| **Spaced repetition no quiz** (Anki-style) | Aluno revisa o que errou há 1/3/7/14 dias. Multiplica retenção sem custo extra de LLM | Médio |
| **Streak diário + meta semanal** | Gamificação leve. Já temos histórico local, falta UI de progresso diário | Baixo |
| **Marcar aula concluída pelo chat** | "Já assisti essa aula" → tutor entende e marca + atualiza histórico (function calling do LLM) | Baixo |
| **Anotações por aula** | Textarea livre por `lesson_id` persistida em localStorage. "Meu caderno" agregado por curso | Baixo |
| **Modo escuro** | Toggle no header, respeita `prefers-color-scheme`. Tailwind já suporta `dark:` | Trivial |
| **Compartilhar plano por link** | URL com payload do plano em base64. "Olha o que estou estudando" | Baixo |
| **PWA installable** | `manifest.json` + service worker leve. Vira "app" no celular | Baixo |
| **Resumo em PDF para download** | Plano + diagnóstico + resumos da IA em um PDF (lib `weasyprint`) | Médio |
| **Chat por voz** | Browser Speech API (entrada) + nosso TTS (saída). Hands-free no carro | Médio |
| **Atalhos de teclado** | J/K navega plano, Enter abre, `?` mostra ajuda, `/` foca chat | Trivial |

---

## 🎯 Médio prazo (1-3 meses)

Exigem alguma modelagem nova, mas dão salto de produto.

### Personalização adaptativa real

- **Detecção do estilo de aprendizagem por comportamento**: se o aluno consome mais áudio que texto, prioriza TTS. Se faz muitos quizzes, prioriza prática. Sem auto-declaração — observa.
- **Ajuste de dificuldade do quiz** com base no histórico de acertos por tópico
- **Recomendação colaborativa**: "alunos com objetivo parecido também fizeram X" (usa o dump de histórico de alunos vindo no Drive atualizado)
- **Memória persistente do tutor** (mem0 / Letta-style): lembra "você me disse semana passada que tem dificuldade com IFRS" entre sessões

### Conteúdo gerado expandido

- **Flashcards gerados** com revisão espaçada (cards extraídos das transcrições)
- **Mapa mental visual** por curso (Mermaid generated)
- **Podcast diário personalizado** — 5 min de áudio resumindo o que o aluno deveria saber hoje, gerado da noite anterior
- **Avaliação dissertativa** — aluno responde por extenso, IA dá nota e feedback (vs múltipla escolha atual)
- **Modo "explique como se..."** — slider iniciante↔expert ajusta complexidade da resposta no chat

### Integração CEFIS aprofundada

- **Sincronizar progresso bidirecional** — marcar aula no tutor reflete na conta CEFIS
- **Inscrição automática** em curso pelo tutor (botão "matricular")
- **Trilhas próprias do aluno** — salvar combinação personalizada como trilha reusável
- **Emissão automática de certificado** quando aluno completa critério (passar `accuracy >= 80%` em todos quizzes do curso)
- **Importar planos de RH** — empresa cria trilha obrigatória, aluno acessa via login corporativo

---

## 🚀 Longo prazo (3-12 meses)

Visão de produto — exigem investimento de equipe.

### IA agente

- **Agente proativo**: detecta que o aluno está parado há 5 dias e envia mensagem ("vamos retomar?")
- **Tutor multi-agente**: um agente "diagnosticador", um "explicador" (RAG), um "examinador" (quiz), um "motivador". Orchestrator escolhe quem fala
- **Geração de conteúdo quando o catálogo não cobre**: tutor cria uma "aula CEFIS-style" totalmente nova com vídeo TTS + slides quando detecta gap real
- **Análise dissertativa profunda** com rubrica configurável pelo professor

### Comunidade

- **Q&A público da comunidade** com voting (StackOverflow-style por curso)
- **Estudar em grupo** — mesma trilha, mesma fase, sincronizada (4 alunos no mesmo PDCA)
- **Mentoria peer-to-peer** matched por nível complementar

### Operacional / negócio

- **Multi-tenant B2B**: empresas com sub-domínio próprio, white-label, dashboard de gestor
- **Marketplace de trilhas** criadas por professores top
- **API pública**: devs constroem em cima (Slack bot, integração LMS, etc)
- **Modelo freemium** com limites de sessões/mês e quiz/mês
- **Compliance educacional**: SCORM, integração com Moodle/Canvas

### Infra

- **Postgres + pgvector** em vez de SQLite (multi-instância, alta disponibilidade)
- **Cache Redis** de respostas frequentes (mesma pergunta de 50 alunos → 1 chamada à OpenAI)
- **Observabilidade**: Sentry + OpenTelemetry, dashboards de uso
- **A/B testing de prompts** — qual versão do `DIAGNOSIS_SYSTEM` engaja mais?
- **Fine-tuning próprio** de modelo pequeno (Qwen 7B) no corpus CEFIS para reduzir custo OpenAI

---

## 📊 Acessibilidade & UX

- Internacionalização (PT-BR / EN / ES)
- WCAG AA: leitor de tela, alto contraste, navegação por teclado completa
- Modo offline parcial: download de aulas + transcrições para o celular
- Tema customizável (escuro, sépia, alto contraste)
- Tradução automática de respostas do chat

---

## 🔒 Segurança & privacidade

- Rate limit por IP/usuário
- Sanitização de input nos prompts (proteção contra prompt injection)
- Cifra de cookies de sessão CEFIS no servidor
- LGPD: política de privacidade, opt-in para uso de dados de progresso para recomendação colaborativa
- Auditoria de chamadas à API CEFIS (timestamps + IPs)

---

## 💡 Curiosidades — ideias mais ousadas

- **"Pergunte ao professor da aula"**: clonar a voz e o estilo do professor (com permissão) e responder no chat como se fosse ele
- **Simulação de prova CRC** com timer, questões oficiais e relatório de prontidão
- **Tutoria peer guiada por IA**: o tutor identifica que dois alunos estão estudando o mesmo tema e sugere conversa entre eles
- **Recomendação preditiva**: "Em 2 semanas vai sair uma nova legislação X — comece a estudar essa aula" (integração com news/Brasília)

---

## Como contribuir

PRs bem-vindos. Antes de começar uma feature grande:

1. Abra uma issue descrevendo o problema/oportunidade
2. Mantenha o padrão atual: zero build no frontend, prompts em `app/prompts.py`, schema em `db.py`
3. Adicione teste E2E em `scripts/test_endpoints.py`
4. Rode `python scripts/test_endpoints.py` antes de PR (9/9 deve continuar passando)
