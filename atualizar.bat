@echo off
REM ============================================================
REM Atualiza o Tutor IA CEFIS no servidor (git pull + deps + restart).
REM Rode como ADMINISTRADOR.
REM ============================================================

cd /d "%~dp0"

REM Confere admin
net session >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Execute como administrador (botao direito -^> Executar como administrador).
    pause
    exit /b 1
)

REM Confere git
where git >nul 2>nul
if errorlevel 1 (
    echo [AVISO] git nao encontrado no PATH.
    echo Voce usou o download ZIP? Entao precisa baixar o novo ZIP e
    echo sobrescrever os arquivos manualmente (preservando .env, data\, .venv\).
    pause
    exit /b 1
)

echo ============================================================
echo Atualizando Tutor IA CEFIS
echo ============================================================
echo.

REM 1. Parar servico
echo [1/5] Parando servico TutorCEFIS...
nssm stop TutorCEFIS
timeout /t 2 >nul

REM 2. Backup do .env por seguranca (nao deve ser sobrescrito mas garante)
if exist .env (
    copy .env .env.bkp >nul
    echo [info] backup do .env criado
)

REM 3. git pull
echo [2/5] Baixando atualizacoes do GitHub...
git fetch --all
git reset --hard origin/main
if errorlevel 1 (
    echo [ERRO] git pull falhou. Veja a mensagem acima.
    nssm start TutorCEFIS
    pause
    exit /b 1
)

REM 3b. restaurar .env se o git removeu por algum motivo
if not exist .env (
    if exist .env.bkp copy .env.bkp .env >nul
    echo [info] .env restaurado do backup
)

REM 4. Atualizar dependencias
echo [3/5] Atualizando dependencias Python...
.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet

REM 5. Reiniciar servico
echo [4/5] Reiniciando servico...
nssm start TutorCEFIS
timeout /t 3 >nul

REM 6. Validar
echo [5/5] Validando...
curl -fsS http://localhost:8000/api/status >nul 2>nul
if errorlevel 1 (
    echo [AVISO] Servico nao respondeu em /api/status. Veja os logs:
    echo     type data\service-err.log
) else (
    echo.
    echo ============================================================
    echo Atualizacao concluida com sucesso!
    echo Servico TutorCEFIS rodando em http://localhost:8000
    echo ============================================================
)

REM Limpa backup se nao precisou
if exist .env if exist .env.bkp del .env.bkp

pause
