# 🛤️ Próximas funcionalidades

Roadmap pós-hackathon, organizado por prazo e impacto. O documento serve como registro do que ainda faz sentido evoluir, assumindo o estado atual como base.

> Estado atual: backend FastAPI (20 rotas), 10/10 testes E2E, deploy em [tutor-cefis.duckdns.org](https://tutor-cefis.duckdns.org). Veja [README.md](README.md) e [ARQUITETURA.md](ARQUITETURA.md).

---

## ✅ Já implementado (até 26/05/2026)

Snapshot do que ficou pronto no hackathon:

### 🎯 Núcleo
- **Onboarding** em 3 passos + seleção manual de cursos candidatos
- **Diagnóstico contextual** ("Mensagem do tutor") que reconhece histórico, cita conceitos dominados e apresenta a sessão atual em 2-3 frases
- **Plano de estudos** com cards diferenciados (Aula CEFIS / Resumo IA / Quiz)
- **Resumos com markdown rico** (headings, listas, negrito, diagramas Mermaid)
- **Welcome screen** com retomada inteligente para quem volta
- **Modal de conclusão de sessão** com opções "Praticar" / "Nova sessão"
- **Loading dinâmico** com 12 etapas em pool + 12 dicas rotativas das features

### 💬 Interação
- **Chat com RAG** em 34.422 chunks vetoriais, citando curso/aula/segundo
- **Áudio TTS** em todo conteúdo gerado pela IA
- **Autoplay** da mensagem do tutor ao iniciar a sessão
- **Chat por voz** com Web Speech API e resposta automática em áudio
- **Roleplay** ("Pratique com o tutor"): IA interpreta personagem, feedback estruturado com nota e aulas recomendadas
- **Voz no roleplay** com TTS automático do personagem
- **Quiz dinâmico** gerado da transcrição real da aula clicada

### 🎓 Gamificação
- **Trajetória de Mestria**: conceito marcado como dominado quando o aluno conclui a aula e acerta ≥80% no quiz
- **Toast discreto** ao dominar novo conceito
- **Insights automáticos**: sessões na semana vs média, melhor período do dia para acerto em quiz, taxa de retenção, conceitos dominados na semana
- Sem streak diário, sem ranking entre alunos — comparativos restritos aos próprios dados do usuário

### 🛤️ Personalização e trilha
- **Histórico cumulativo** em localStorage (aulas, quizzes com nota, cursos, planos, conceitos)
- **Nova sessão recorrente** "tenho X minutos agora" — continuar mesmo objetivo ou trocar de tema
- **Trilha multi-fase**: cada sessão concluída libera próxima fase, excluindo automaticamente o que já foi visto
- **Trilhas oficiais CEFIS** via API real (`/tracks`) como atalho ao objetivo livre
- **Resumos linkam para aulas reais** ("Para se aprofundar:")

### 🔗 Integração CEFIS (5 endpoints)
- `POST /api/v1/login` + `GET /api/v1/user/me`
- `GET /performance/certificates` (remove cursos já certificados do plano)
- `GET /tracks` + `GET /tracks/:id` (trilhas oficiais)
- `GET /courses/:id/lessons` com progress real ("continue de onde parou")

### 🎨 UX / produto
- **Modo escuro** com toggle persistente
- **Logos CEFIS oficiais** em todas as telas
- **Slug correto** nas URLs (`/curso/{slug}/{id}`)
- **Perfil persistente** em localStorage (sobrevive refresh)
- **Dashboard "Meu Progresso"** com cards de stats + trajetória + insights

### ⚙️ Operacional
- **Deploy público** Windows Server + IIS + nssm + Let's Encrypt
- **Scripts .bat** para indexar, iniciar, instalar serviço, atualizar
- **10/10 testes E2E** automatizados ([scripts/test_endpoints.py](scripts/test_endpoints.py))
- **Validação Playwright** real no browser (chat, modal, dark mode)

---

## ⚡ Curto prazo (1-2 semanas cada)

Itens que cabem na arquitetura atual sem refatoração relevante.

| Item | Descrição | Esforço |
|---|---|---|
| **Spaced repetition no quiz** | Aluno revisa perguntas erradas em 1/3/7/14 dias. Aplicação do algoritmo SM-2 sobre o histórico de quizzes | Médio |
| **Ritmo voluntário** | Aluno define ritmo desejado (1-2x/sem, 2-3x/sem, diário) e vê comparativo no Meu Progresso. Inclui modo pausa | Baixo |
| **Marcos com certificado PDF** | Ao atingir critérios (ex: trilha concluída), oferece download de PDF + compartilhamento no LinkedIn (`jspdf` via CDN) | Médio |
| **Marcar aula concluída pelo chat** | Function calling do LLM detecta intenção e marca como concluída | Baixo |
| **Anotações por aula** | Textarea livre por `lesson_id` persistida em localStorage; visão agregada em "Meu caderno" | Baixo |
| **Compartilhar plano por link** | URL com payload do plano em base64 para envio a terceiros | Baixo |
| **PWA installable** | `manifest.json` + service worker para instalação no celular | Baixo |
| **Resumo em PDF para download** | Plano + mensagem do tutor + resumos da IA exportados em PDF | Médio |
| **Atalhos de teclado** | J/K navega plano, Enter abre, `?` ajuda, `/` foca chat | Trivial |

---

## 🎯 Médio prazo (1-3 meses)

### Personalização adaptativa

- **Detecção do estilo de aprendizagem por comportamento**: observação de consumo (áudio vs texto vs prática) ajusta a recomendação de conteúdo sem auto-declaração
- **Ajuste dinâmico de dificuldade do quiz** com base no histórico de acertos por tópico
- **Recomendação colaborativa**: agrupa alunos por similaridade de objetivo e sugere conteúdo bem avaliado por pares
- **Memória persistente do tutor** (mem0 / Letta-style): retém preferências e dificuldades entre sessões

### Conteúdo gerado expandido

- **Flashcards** com revisão espaçada (cards extraídos das transcrições)
- **Podcast diário personalizado**: 5 min de áudio gerado da noite anterior com o conteúdo do dia
- **Avaliação dissertativa**: aluno responde por extenso, IA aplica rubrica e retorna nota + feedback
- **Slider de profundidade**: ajusta a complexidade da resposta no chat entre iniciante e especialista

### Integração CEFIS aprofundada

- **Sincronização de progresso bidirecional**: marcar aula no tutor reflete na conta CEFIS
- **Inscrição automática** em curso a partir do tutor
- **Trilhas próprias do aluno** salvas e reutilizáveis
- **Emissão automática de certificado** ao completar critério
- **Trilhas corporativas**: empresas configuram trilha obrigatória, aluno acessa via login corporativo

---

## 🚀 Longo prazo (3-12 meses)

### IA agente

- **Agente proativo**: detecta inatividade prolongada e propõe sessão curta
- **Tutor multi-agente**: diagnosticador, explicador (RAG), examinador (quiz) e motivador coordenados por orquestrador
- **Geração de aula nova** quando o catálogo não cobre o assunto: vídeo TTS + slides gerados pela IA
- **Avaliação dissertativa profunda** com rubrica configurável pelo professor

### Comunidade

- **Q&A público da comunidade** com voting (StackOverflow-style por curso)
- **Estudar em grupo** — mesma trilha, mesma fase, sincronizada
- **Mentoria peer-to-peer** matched por nível complementar

### ⚙️ Operacional / negócio

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

## ♿ Acessibilidade e UX

- Internacionalização (PT-BR, EN, ES)
- WCAG AA: leitor de tela, alto contraste, navegação por teclado completa
- Modo offline parcial: download de aulas e transcrições para o celular
- Tema customizável (escuro, sépia, alto contraste)

---

## 🔒 Segurança e privacidade

- Rate limit por IP e por usuário
- Sanitização de input nos prompts contra prompt injection
- Cifra de cookies de sessão CEFIS no servidor
- LGPD: política de privacidade e opt-in para uso de dados de progresso em recomendação colaborativa
- Auditoria de chamadas à API CEFIS (timestamps e IPs)

---

## 💡 Exploratórias

- **"Pergunte ao professor da aula"**: voz e estilo do professor (com autorização) usados como persona do chat
- **Simulação de prova CRC** com timer, questões oficiais e relatório de prontidão
- **Tutoria entre pares guiada por IA**: identifica alunos no mesmo tema e sugere troca
- **Recomendação preditiva**: novas legislações ou mudanças no setor disparam sugestões de estudo antecipado
- **Modo apresentação**: aluno termina trilha e a IA gera slides para apresentar à equipe

---

## 🎨 Princípios de design adotados

- Mestria mensurável em vez de pontos abstratos
- Auto-comparação em vez de ranking social
- Insights úteis em vez de notificações de pressão
- Linguagem adulta e profissional nos textos da interface
- Recompensa funcional (desbloqueio de conteúdo) em vez de cosmética
- Tutor que reconhece o aluno em vez de diagnóstico genérico

Esses princípios orientam as próximas decisões de produto.

---

## 🤝 Como contribuir

PRs bem-vindos. Antes de começar uma feature grande:

1. Abra uma issue descrevendo o problema/oportunidade
2. Mantenha o padrão atual: zero build no frontend, prompts em `app/prompts.py`, schema em `db.py`
3. Adicione teste E2E em `scripts/test_endpoints.py`
4. Rode `python scripts/test_endpoints.py` antes de PR (10/10 deve continuar passando)
