@echo off
REM ============================================================
REM Para e remove o servico TutorCEFIS.
REM Rode como administrador.
REM ============================================================

set SVCNAME=TutorCEFIS

net session >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Execute como administrador.
    pause
    exit /b 1
)

where nssm >nul 2>nul
if errorlevel 1 (
    echo [ERRO] nssm.exe nao encontrado no PATH.
    pause
    exit /b 1
)

echo Parando %SVCNAME%...
nssm stop %SVCNAME% 2>nul

echo Removendo %SVCNAME%...
nssm remove %SVCNAME% confirm

echo.
echo Servico removido.
pause
