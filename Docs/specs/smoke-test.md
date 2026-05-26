# Smoke test — Tutor IA CEFIS

Validar o fluxo ponta a ponta antes da entrega.

## Pré-requisitos
- [ ] Indexação concluída (`data/index_state.json` existe)
- [ ] `iniciar.bat` rodando em um cmd
- [ ] Browser aberto em http://localhost:8000

## 1. Tela inicial
- [ ] Vai **direto pro onboarding** (não fica na tela de "preparando o tutor")
- [ ] Logo CEFIS + título "Seu tutor pessoal de aprendizado"
- [ ] Link no rodapé: "Já tem conta CEFIS? Entre para personalizar..."

## 2. Onboarding — Passo 1 (nome + áreas)
- [ ] Campo nome aceita texto
- [ ] Cards de áreas marcam/desmarcam ao clicar
- [ ] Botão "Continuar" só habilita com nome + 1+ área
- [ ] Voltar para a tela e digitar nome → ainda preenchido? (teste persistência)

## 3. Onboarding — Passo 2 (objetivo)
- [ ] Textarea aceita texto livre
- [ ] Box azul com dica aparece
- [ ] "Continuar" só habilita com >10 caracteres
- [ ] Botão "← Voltar" funciona

## 4. Onboarding — Passo 3 (nível + tempo)
- [ ] 3 botões de nível selecionáveis
- [ ] Slider de tempo move de 10min até 40h
- [ ] Label do tempo atualiza em tempo real ("1h 30min")
- [ ] Botão "Gerar meu plano ✨" só habilita com tudo preenchido

## 5. Geração do plano
- [ ] Tela "Montando seu plano" aparece com etapas animadas
- [ ] Em ~5-15s aparece a tela do plano
- [ ] **Diagnóstico** (parágrafo azul) menciona seu nome ou objetivo
- [ ] Lista de itens do plano tem pelo menos 1 **🎬 Aula CEFIS** e pelo menos 1 **📝 Resumo IA**
- [ ] Duração total ≤ tempo declarado + 10%
- [ ] Cada item tem ícone, badge, duração, motivo (💡), professor (para aulas)

## 6. Links dos cursos
- [ ] Clicar em "Assistir →" em uma **aula** abre nova aba
- [ ] URL no formato: `cefis.com.br/curso/{slug}/{id}`
- [ ] A página da CEFIS abre o curso **certo** (título bate)

## 7. Marcar como concluído
- [ ] Clicar no checkbox de um item → fica verde, texto riscado
- [ ] Contador "X/Y" no topo atualiza
- [ ] F5 (refresh) → item volta a estar marcado? (stretch, não obrigatório)

## 8. Chat com RAG
- [ ] Mensagem inicial do tutor cita seu nome
- [ ] Digite uma pergunta sobre um tópico do seu plano (ex.: "o que é PDCA?")
- [ ] Resposta aparece **em streaming** (token por token, não de uma vez)
- [ ] Bolinhas animadas enquanto carrega
- [ ] Resposta tem seção **"Fontes:"** com 1-6 links
- [ ] Clicar em uma fonte abre o curso correto na CEFIS
- [ ] Fontes mostram **segundo aproximado** (ex.: "2:35")

## 9. Login CEFIS (opcional)
- [ ] No onboarding, link "Já tem conta CEFIS?" abre modal
- [ ] Modal tem campos email/CPF + senha
- [ ] Submeter com credenciais válidas → modal fecha
- [ ] Aparece banner verde "Conectado como **{Seu Nome}**"
- [ ] Se você for premium, aparece badge amarelo "Premium"
- [ ] Nome auto-preenchido (se estava vazio)
- [ ] Áreas auto-preenchidas com match das suas `activities`
- [ ] Gerar plano novamente → cursos já certificados **não aparecem**
- [ ] Botão "Sair" remove o banner mas mantém o que você preencheu

## 10. Persistência (F5)
- [ ] Preencher onboarding até passo 3 e dar F5
- [ ] Voltar → nome, áreas, objetivo, nível, tempo: tudo preservado
- [ ] Login persiste via cookie (continua logado)

## 11. Erros graciosos
- [ ] Tentar gerar plano com OPENAI_API_KEY inválida → mensagem de erro clara, UI volta pro onboarding
- [ ] Chat sem internet (desligue wifi) → mensagem de erro, não trava

---

## Bugs encontrados / observações

> Anote aqui o que aparecer:

| # | Severidade | Descrição |
|---|---|---|
|   |            |           |

---

## Veredito final

- [ ] **Tudo OK** — pode gravar o vídeo
- [ ] Bugs pequenos — corrigir antes do vídeo
- [ ] Bug crítico — corrigir e re-testar
