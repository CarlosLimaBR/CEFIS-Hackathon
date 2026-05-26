@echo off
REM ============================================================
REM Inicia o servidor FastAPI do Tutor IA CEFIS (modo local).
REM Acesse http://localhost:8000 depois que subir.
REM Ctrl+C para parar.
REM ============================================================

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] venv nao encontrada. Rode:
    echo     python -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERRO] .env nao encontrado. Copie .env.example e preencha.
    pause
    exit /b 1
)

echo ============================================================
echo Tutor IA CEFIS - servidor local
echo ============================================================
echo Acesse: http://localhost:8000
echo Ctrl+C para parar
echo.

".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
