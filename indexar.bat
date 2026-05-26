@echo off
REM ============================================================
REM Indexa as transcricoes da CEFIS em SQLite + sqlite-vec.
REM Use este arquivo no command prompt (cmd).
REM Pode interromper com Ctrl+C e rodar de novo - retoma do ponto.
REM ============================================================

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] venv nao encontrada em .venv\
    echo Crie o venv primeiro:
    echo     python -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERRO] .env nao encontrado.
    echo Copie .env.example para .env e preencha OPENAI_API_KEY.
    pause
    exit /b 1
)

echo ============================================================
echo Iniciando indexacao das transcricoes CEFIS
echo ============================================================
echo.
echo Catalogo: Docs\output\ (476 cursos, ~34k chunks)
echo Modelo:   text-embedding-3-small
echo Custo:    ~$0.17 estimado
echo Tempo:    15-25 minutos
echo.
echo Voce pode interromper com Ctrl+C - o script retoma do ponto.
echo.

".venv\Scripts\python.exe" scripts\index_transcripts.py %*

echo.
echo ============================================================
echo Indexacao finalizada (ou interrompida).
echo Confira data\index_state.json para o relatorio final.
echo ============================================================
pause
