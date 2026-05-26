# Roteiro do vídeo demo

**Duração alvo:** 90 segundos (até 2 min).
**Ferramentas sugeridas (grátis):**
- **OBS Studio** ([obsproject.com](https://obsproject.com/)) — captura tela + mic em alta qualidade
- **Loom** ([loom.com](https://www.loom.com/)) — captura + link pronto sem editar

**Resolução:** grave em 1080p (1920×1080). YouTube/Loom aceitam.

---

## Antes de gravar

- [ ] Servidor `iniciar.bat` rodando
- [ ] Browser limpo: aba só com http://localhost:8000
- [ ] Limpar `localStorage` (DevTools → Application → Local Storage → Delete) para começar com onboarding zerado
- [ ] Fazer logout do CEFIS no app (botão "Sair") para mostrar o fluxo de login
- [ ] Ter uma pergunta pronta para o chat (algo concreto do plano que será gerado)
- [ ] Fechar Slack/notificações
- [ ] Testar nível do áudio do mic

---

## Script (fale natural, sem ler)

### 🎬 0:00–0:10 — Abertura
> "Oi, sou Carlos. Esse é o **Tutor IA CEFIS**, meu projeto pro hackathon. Em 1 dia entreguei um tutor que **conhece o aluno, identifica lacunas e monta um plano personalizado** combinando o catálogo real da CEFIS com conteúdo gerado pela IA."

**Tela:** página inicial (onboarding passo 1)

### 🎬 0:10–0:30 — Onboarding rápido
> "O onboarding tem 3 passos. Eu coloco meu nome, áreas de interesse — Gestão e RH —, meu objetivo: 'quero entender PDCA e melhoria contínua em 30 minutos', sou intermediário, tenho **30 minutos**."

**Ação:** preencher os 3 passos rápido (use auto-preenchimento se já tiver). Clicar "Gerar meu plano".

### 🎬 0:30–0:55 — O plano + diagnóstico
> "A IA gera o **diagnóstico** — explica o gap em prosa — e monta um plano que **respeita meu tempo**. Cada item é marcado: **🎬 Aula CEFIS** quando vem do catálogo real, **📝 Resumo IA** quando o catálogo não cobre e a IA gera. Isso atende dois critérios do briefing: integração CEFIS e geração de conteúdo original."

**Ação:** scroll mostrando o plano. Apontar 1 aula CEFIS e 1 resumo IA.

### 🎬 0:55–1:10 — Click no curso real
> "Os links abrem o **curso real** na CEFIS — não é mock."

**Ação:** clicar em "Assistir →" em uma aula → nova aba carrega cefis.com.br/curso/...

### 🎬 1:10–1:35 — Chat com RAG (DIFERENCIAL)
> "Agora o diferencial: o chat. Eu indexei **as 7.447 transcrições reais das aulas** — 34 mil chunks vetoriais. Quando pergunto algo, a IA responde **citando o segundo exato da aula** que tem aquela informação."

**Ação:** digitar "explica PDCA em 1 parágrafo". Mostrar streaming + fontes clicáveis no rodapé da resposta.

### 🎬 1:35–1:50 — Login CEFIS (análise retroativa)
> "Se eu entrar com minha conta CEFIS, o tutor puxa os **cursos que eu já fiz** e remove do plano. Não fica recomendando o que eu já sei."

**Ação:** abrir modal "Já tem conta CEFIS?", logar, mostrar badge "Conectado como Carlos · Premium".

### 🎬 1:50–2:00 — Fecho
> "Stack: **Python + FastAPI + SQLite + OpenAI**. Roda em qualquer servidor Windows como serviço, ou em Docker. Código no GitHub. Obrigado."

**Tela:** mostrar README do GitHub ou tela de plano com chat

---

## Diferenciais para destacar no vídeo (escolher 3)

1. **RAG profundo nas transcrições** — o chat cita curso, aula e segundo exato onde a informação é dita
2. **Catálogo 100% local indexado** — zero rate limit, busca semântica instantânea
3. **Login CEFIS real** — remove cursos já certificados do plano
4. **Combinação explícita CEFIS + IA** — badges 🎬 / 📝 no plano
5. **"Instala em qualquer servidor"** — nssm + Docker
6. **Spec lógica + protótipo antes do código** — documentado no repo

## O que NÃO mostrar

- Erros, bugs ou loadings longos (gravar de novo se acontecer)
- Detalhes técnicos de código (a banca quer ver o produto)
- "Stretch goals que não fiz" — não confessar lacunas
- Configuração / setup — pular direto pro produto rodando

---

## Após gravar

- [ ] Subir no YouTube (unlisted) ou Loom
- [ ] Copiar link para o README na seção "Demo"
- [ ] Postar no formulário/grupo do hackathon (conforme instruções da CEFIS)
