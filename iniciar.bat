@echo off
title Prospecção WhatsApp
echo Iniciando Prospecção WhatsApp...
echo.

REM Usa o diretório onde o script está localizado
cd /d "%~dp0"

echo Diretório atual: %cd%
echo.

REM Verifica se o ambiente virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo ERRO: Pasta 'venv' não encontrada neste diretório!
    echo Certifique-se que o ambiente virtual foi criado.
    echo.
    pause
    exit /b
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERRO: Não foi possível ativar o ambiente virtual!
    echo.
    pause
    exit /b
)

echo Verificando se interface.py existe...
if not exist "interface.py" (
    echo ERRO: Arquivo 'interface.py' não encontrado!
    echo Certifique-se que o arquivo está nesta pasta.
    echo.
    pause
    exit /b
)

echo Ambiente ativado. Iniciando interface...
echo.
pythonw interface.py

if errorlevel 1 (
    echo.
    echo ERRO: Não foi possível iniciar a interface!
    echo Verifique as mensagens de erro acima.
    echo.
)

echo.
echo Interface iniciada. Verifique a janela da aplicação.