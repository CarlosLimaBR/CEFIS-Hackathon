# Deploy no servidor 192.169.179.16 (C:\TutorCEFIS)

Passo a passo para colocar o Tutor IA CEFIS no ar nesse servidor Windows com IIS já configurado como reverse proxy.

## Cenário esperado

```
Internet → HTTPS (IIS porta 443) → reverse proxy → http://localhost:8000 (uvicorn)
```

O `web.config` que você instalou já faz o reverse proxy de tudo (`/*`) para `localhost:8000`.

## Pré-requisitos no servidor

Você já tem:
- ✅ Python 3.11+ instalado
- ✅ IIS rodando com URL Rewrite + Application Request Routing
- ✅ web.config em C:\TutorCEFIS\ apontando para `localhost:8000`

Falta:
- ⬜ Git para Windows ([git-scm.com/download/win](https://git-scm.com/download/win))
- ⬜ nssm.exe ([nssm.cc/download](https://nssm.cc/download)) — coloque em `C:\Windows\System32`
- ⬜ Liberar `localhost:8000` (já é local — não precisa de firewall extra)

---

## Passo a passo (uma vez só)

### 1. Abra um **Prompt de Comando como Administrador**

### 2. Clonar o repo

```cmd
cd C:\TutorCEFIS
git clone https://github.com/CarlosLimaBR/CEFIS-Hackathon.git .
```

> O ponto final clona pra dentro do diretório atual sem criar subpasta. Se C:\TutorCEFIS tiver arquivos (tipo o web.config), use:
> ```cmd
> git clone https://github.com/CarlosLimaBR/CEFIS-Hackathon.git temp
> xcopy temp\* . /E /H /K /Y
> rmdir /S /Q temp
> ```

### 3. Extrair o catálogo

```cmd
cd C:\TutorCEFIS\Docs
powershell -Command "Expand-Archive -Path courses.zip -DestinationPath output -Force"
```

> Cria `Docs\output\` com 476 pastas de curso. Demora ~30s.

### 4. Criar venv e instalar dependências

```cmd
cd C:\TutorCEFIS
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 5. Configurar `.env`

```cmd
copy .env.example .env
notepad .env
```

Preencha `OPENAI_API_KEY` com a chave da OpenAI. Salve.

> ⚠️ Se a chave que estamos usando agora foi exposta no chat, **gere uma nova** em [platform.openai.com/api-keys](https://platform.openai.com/api-keys) e revogue a antiga.

### 6. Indexar transcrições (~20 minutos, custo ~$0.17)

```cmd
indexar.bat
```

Aguarde até ver `Indexacao finalizada`. Verifique:

```cmd
type data\index_state.json
```

Deve mostrar `"embeddings": 34422`.

### 7. Testar local (antes de virar serviço)

```cmd
iniciar.bat
```

Em outro cmd, valide:

```cmd
curl http://localhost:8000/api/status
```

Deve retornar JSON com `"ready": true`. Pare com `Ctrl+C`.

### 8. Instalar como serviço Windows

```cmd
cd C:\TutorCEFIS
instalar-servico.bat
```

O script registra o serviço `TutorCEFIS` com autostart e log rotativo.

### 9. Validar pelo IIS

Abra no browser:

```
https://192.169.179.16/api/status
```

Deve retornar JSON. Se sim, abra a raiz:

```
https://192.169.179.16/
```

A SPA do tutor aparece.

---

## Operações

```cmd
nssm status TutorCEFIS                                REM ver se esta rodando
nssm restart TutorCEFIS                               REM reiniciar
type C:\TutorCEFIS\data\service-err.log               REM ver erros
C:\TutorCEFIS\.venv\Scripts\python.exe ^
    C:\TutorCEFIS\scripts\test_endpoints.py ^
    http://localhost:8000                             REM rodar testes contra o serviço
```

## Atualizar código mais tarde

```cmd
cd C:\TutorCEFIS
nssm stop TutorCEFIS
git pull
.venv\Scripts\python.exe -m pip install -r requirements.txt
nssm start TutorCEFIS
```

---

## Troubleshooting

**`502 Bad Gateway` no IIS:**
- O serviço uvicorn não está rodando. `nssm status TutorCEFIS`. Veja `data\service-err.log`.

**`Indice nao pronto` na UI:**
- Você esqueceu de rodar `indexar.bat`. Faça e reinicie o serviço.

**Chat trava:**
- Problema com OpenAI API. Veja `data\service-err.log` por mensagens de rate-limit ou 401.

**URL Rewrite não funciona:**
- Confirme que o módulo URL Rewrite + Application Request Routing estão instalados no IIS. Habilite proxy em IIS Manager → Application Request Routing Cache → Server Proxy Settings → "Enable proxy".

**SSL / certificado:**
- Se for IP, o browser vai reclamar de cert auto-assinado. Para domínio público, use Let's Encrypt via `win-acme`.
