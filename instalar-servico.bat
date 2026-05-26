@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM ============================================================
REM Instala o Tutor IA CEFIS como SERVICO do Windows via nssm.
REM
REM Pre-requisitos:
REM   1) Python 3.11+ instalado
REM   2) venv criada: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
REM   3) .env preenchido com OPENAI_API_KEY
REM   4) Indice ja gerado (rode indexar.bat antes)
REM   5) nssm.exe no PATH (https://nssm.cc/download)
REM
REM Rode como ADMINISTRADOR. Apos instalar, o servico sobe sozinho no boot.
REM ============================================================

set SVCNAME=TutorCEFIS
set PROJDIR=%~dp0
if "%PROJDIR:~-1%"=="\" set PROJDIR=%PROJDIR:~0,-1%

echo ============================================================
echo Instalacao do servico %SVCNAME%
echo Diretorio: %PROJDIR%
echo ============================================================
echo.

REM Confere se esta rodando como admin
net session >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Este script precisa ser executado como Administrador.
    echo Clique com o botao direito em instalar-servico.bat -^> Executar como administrador.
    pause
    exit /b 1
)

REM Confere nssm
where nssm >nul 2>nul
if errorlevel 1 (
    echo [ERRO] nssm.exe nao encontrado no PATH.
    echo.
    echo Baixe em: https://nssm.cc/download
    echo Coloque o nssm.exe em C:\Windows\System32 ou adicione ao PATH.
    pause
    exit /b 1
)

REM Confere venv
if not exist "%PROJDIR%\.venv\Scripts\python.exe" (
    echo [ERRO] venv nao encontrada em %PROJDIR%\.venv
    echo Crie antes:
    echo     python -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

REM Confere .env
if not exist "%PROJDIR%\.env" (
    echo [ERRO] .env nao encontrado.
    echo Copie .env.example para .env e preencha OPENAI_API_KEY.
    pause
    exit /b 1
)

REM Se ja existe, remove para reinstalar limpo
sc query %SVCNAME% >nul 2>nul
if not errorlevel 1 (
    echo Servico %SVCNAME% ja existe. Parando e removendo para reinstalar...
    nssm stop %SVCNAME% >nul 2>nul
    nssm remove %SVCNAME% confirm >nul
    timeout /t 2 >nul
)

REM Garante pasta de logs
if not exist "%PROJDIR%\data" mkdir "%PROJDIR%\data"

echo Registrando servico...
nssm install %SVCNAME% "%PROJDIR%\.venv\Scripts\python.exe" "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"
nssm set %SVCNAME% AppDirectory "%PROJDIR%"
nssm set %SVCNAME% DisplayName "Tutor IA CEFIS"
nssm set %SVCNAME% Description "Tutor personalizado de aprendizado com IA (hackathon CEFIS 2026)"
nssm set %SVCNAME% Start SERVICE_AUTO_START
nssm set %SVCNAME% AppStdout "%PROJDIR%\data\service-out.log"
nssm set %SVCNAME% AppStderr "%PROJDIR%\data\service-err.log"
nssm set %SVCNAME% AppRotateFiles 1
nssm set %SVCNAME% AppRotateOnline 1
nssm set %SVCNAME% AppRotateBytes 10485760
nssm set %SVCNAME% AppEnvironmentExtra PYTHONUNBUFFERED=1

echo.
echo Iniciando servico...
nssm start %SVCNAME%
timeout /t 3 >nul

sc query %SVCNAME% | findstr "RUNNING" >nul
if errorlevel 1 (
    echo.
    echo [AVISO] Servico nao subiu. Veja:
    echo     %PROJDIR%\data\service-err.log
) else (
    echo.
    echo ============================================================
    echo Servico instalado e RODANDO.
    echo Acesse: http://localhost:8000
    echo.
    echo Logs: %PROJDIR%\data\service-*.log
    echo Parar: nssm stop %SVCNAME%
    echo Remover: desinstalar-servico.bat
    echo ============================================================
)
pause
