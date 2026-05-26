# Deploy no servidor Windows 192.169.179.16

Guia operacional. Tempo total estimado: 40 a 50 minutos, dos quais cerca de 25 minutos correspondem à indexação rodando em background.

> Pré-condições: Python 3.11+, IIS com URL Rewrite e ARR habilitados, `web.config` em `C:\TutorCEFIS` configurado como reverse proxy para `localhost:8000`.

---

## Checklist

```
[ ] 1. Instalar nssm.exe (5 min)
[ ] 2. Instalar Git para Windows (5 min) ou usar Download ZIP
[ ] 3. Clonar o repositório em C:\TutorCEFIS (2 min)
[ ] 4. Extrair Docs\courses.zip (1 min)
[ ] 5. Criar venv e instalar dependências (3 min)
[ ] 6. Criar .env com OPENAI_API_KEY válida (2 min)
[ ] 7. Rodar indexar.bat (~25 min, custo ~$0.17 em embeddings)
[ ] 8. Testar localmente com curl em localhost:8000 (1 min)
[ ] 9. Instalar como serviço Windows via instalar-servico.bat (1 min)
[ ] 10. Validar acesso pelo IIS em https://192.169.179.16 (1 min)
```

---

## Passos detalhados

### 1. Instalar nssm

1. Baixe https://nssm.cc/release/nssm-2.24.zip
2. Extraia, copie `nssm-2.24/win64/nssm.exe` para `C:\Windows\System32\`
3. Em um cmd: `nssm --version` (deve mostrar "NSSM 2.24...")

### 2. Instalar Git (opcional — alternativa: ZIP direto)

**Com Git:**
- https://git-scm.com/download/win — instalador "next-next-finish" com defaults

**Sem Git (mais simples):**
- Vá em https://github.com/CarlosLimaBR/CEFIS-Hackathon → botão verde "Code" → "Download ZIP"
- Extraia para `C:\TutorCEFIS` (que o conteúdo da pasta `CEFIS-Hackathon-main` vá para dentro de `C:\TutorCEFIS`)

### 3. Clonar (se escolheu Git)

```cmd
cd C:\
git clone https://github.com/CarlosLimaBR/CEFIS-Hackathon.git TutorCEFIS
```

⚠️ Se `C:\TutorCEFIS` já existe com o `web.config`, faça:

```cmd
move C:\TutorCEFIS\web.config C:\web.config.bkp
rmdir C:\TutorCEFIS
cd C:\
git clone https://github.com/CarlosLimaBR/CEFIS-Hackathon.git TutorCEFIS
move C:\web.config.bkp C:\TutorCEFIS\web.config
```

### 4. Extrair o catálogo

```cmd
cd C:\TutorCEFIS\Docs
powershell -Command "Expand-Archive -Path courses.zip -DestinationPath output -Force"
dir output | findstr /R "^.* DIR" | find /c "DIR"
```

Deve mostrar **478** (476 cursos + . + ..). Se mostrar 0 ou 2, deu errado.

### 5. Venv + deps

```cmd
cd C:\TutorCEFIS
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Demora ~2 min para baixar tudo (FastAPI, uvicorn, openai, sqlite-vec...).

### 6. Configurar `.env`

```cmd
copy .env.example .env
notepad .env
```

Substitua a linha:
```
OPENAI_API_KEY=sk-proj-COLE_SUA_CHAVE_AQUI
```
por:
```
OPENAI_API_KEY=sk-proj-<NOVA_KEY>
```

⚠️ **Gere uma chave nova** em https://platform.openai.com/api-keys (a antiga foi exposta no chat — revogue depois). Salve o `.env` e feche o notepad.

### 7. Indexar (uma vez só)

```cmd
indexar.bat
```

Aguarde até ver `Indexacao finalizada`. Vai pedir confirmação no final (`Pressione qualquer tecla...`) — aperte.

Validação:
```cmd
type data\index_state.json
```
Deve ter `"embeddings": 34422`.

### 8. Testar local antes do serviço

```cmd
iniciar.bat
```

Em **outro cmd**:
```cmd
curl http://localhost:8000/api/status
```

Deve mostrar JSON com `"ready": true`. Volte ao cmd do `iniciar.bat` e dê `Ctrl+C` para parar.

### 9. Instalar como serviço

Abra **um novo cmd como Administrador** (botão direito → "Executar como administrador"):

```cmd
cd C:\TutorCEFIS
instalar-servico.bat
```

Vai registrar o serviço `TutorCEFIS`, autostart, log rotativo em `data\service-*.log`.

Validação:
```cmd
sc query TutorCEFIS
```
Deve mostrar `STATE : 4  RUNNING`.

### 10. Acessar pelo IIS

Abra no browser **da sua máquina** (não do servidor):
```
https://192.169.179.16/api/status
```

Deve retornar JSON. Se der erro de certificado, aceite (é IP, não tem cert oficial).

Depois:
```
https://192.169.179.16/
```

A SPA do tutor carrega.

---

## Pós-deploy — operações

| Comando | O que faz |
|---|---|
| `sc query TutorCEFIS` | Ver estado |
| `nssm restart TutorCEFIS` | Reiniciar serviço |
| `type C:\TutorCEFIS\data\service-err.log` | Ver erros |
| `nssm stop TutorCEFIS` | Parar |
| `C:\TutorCEFIS\.venv\Scripts\python.exe C:\TutorCEFIS\scripts\test_endpoints.py http://localhost:8000` | Rodar testes E2E contra o serviço |

## Atualizar código depois

```cmd
nssm stop TutorCEFIS
cd C:\TutorCEFIS
git pull
.venv\Scripts\python.exe -m pip install -r requirements.txt
nssm start TutorCEFIS
```

---

## Troubleshooting

**`502 Bad Gateway`:** serviço caiu. `sc query TutorCEFIS` e veja `service-err.log`.

**`Indice nao pronto` na UI:** esqueceu o passo 7 (indexar). Faça e `nssm restart TutorCEFIS`.

**URL Rewrite não proxia:** abra IIS Manager → server → "Application Request Routing Cache" → "Server Proxy Settings" → marque "Enable proxy" → Apply.

**Chat trava:** problema OpenAI (rate limit, 401). Veja `service-err.log`.

**Quer expor com domínio + HTTPS válido:** use `win-acme` para Let's Encrypt no IIS.
