@echo off
SETLOCAL ENABLEEXTENSIONS

REM ============================================================
REM Atualiza o Tutor IA CEFIS no servidor (git pull + deps + restart).
REM Rode como ADMINISTRADOR.
REM ============================================================

cd /d "%~dp0"

REM 0) Confere admin
net session >nul 2>nul
if errorlevel 1 goto noadmin

REM 0) Confere git
where git >nul 2>nul
if errorlevel 1 goto nogit

echo ============================================================
echo Atualizando Tutor IA CEFIS
echo ============================================================
echo.

echo [1/5] Parando servico TutorCEFIS...
nssm stop TutorCEFIS
timeout /t 2 >nul

REM backup do .env por seguranca
if exist .env copy .env .env.bkp >nul

echo [2/5] Baixando atualizacoes do GitHub...
git fetch --all
git reset --hard origin/main
if errorlevel 1 goto failed_pull

REM restaura .env se git removeu
if not exist .env if exist .env.bkp copy .env.bkp .env >nul

echo [3/5] Atualizando dependencias Python...
.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet

echo [4/5] Reiniciando servico...
nssm start TutorCEFIS
timeout /t 3 >nul

echo [5/5] Validando /api/status...
curl -fsS http://localhost:8000/api/status >nul 2>nul
if errorlevel 1 goto svc_warn

echo.
echo ============================================================
echo Atualizacao concluida com sucesso.
echo Servico TutorCEFIS rodando em http://localhost:8000
echo ============================================================
if exist .env.bkp del .env.bkp
goto end

:noadmin
echo [ERRO] Execute como administrador.
echo Botao direito em atualizar.bat e "Executar como administrador".
goto end

:nogit
echo [AVISO] git nao encontrado no PATH.
echo Voce usou Download ZIP? Entao baixe o ZIP novo manualmente:
echo   https://github.com/CarlosLimaBR/CEFIS-Hackathon/archive/refs/heads/main.zip
echo Sobrescreva os arquivos preservando: .env data .venv Docs\output
goto end

:failed_pull
echo [ERRO] git pull falhou. Reiniciando servico antigo.
nssm start TutorCEFIS
goto end

:svc_warn
echo [AVISO] Servico nao respondeu em /api/status. Diagnostique:
echo     type data\service-err.log

:end
pause
endlocal
