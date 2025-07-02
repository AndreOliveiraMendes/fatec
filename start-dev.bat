@echo off
setlocal enabledelayedexpansion

echo ===============================
echo 🔧 Configurando Git...
echo ===============================

if "%GIT_USER_NAME%"=="" (
    echo Erro: GIT_USER_NAME não está definido.
    exit /b
)
if "%GIT_USER_EMAIL%"=="" (
    echo Erro: GIT_USER_EMAIL não está definido.
    exit /b
)

git config --global user.name "%GIT_USER_NAME%"
git config --global user.email "%GIT_USER_EMAIL%"
git config --global credential.helper manager-core

echo ===============================
echo 🔎 Verificando Python 3.12...
echo ===============================

py -0 | findstr "3.12" >nul
if errorlevel 1 (
    echo ❌ Python 3.12 não encontrado!
    exit /b
) else (
    echo ✅ Python 3.12 encontrado.
)

echo ===============================
echo 🐍 Criando ambiente virtual...
echo ===============================

if not exist .venv (
    py -3.12 -m venv .venv
    echo Ambiente virtual criado com sucesso.
) else (
    echo O ambiente virtual já existe.
)

echo ===============================
echo 🔄 Verificando se o ambiente virtual está ativo...
echo ===============================

if defined VIRTUAL_ENV (
    echo O ambiente virtual já está ativo.
) else (
    echo Ativando o ambiente virtual...
    call .venv\Scripts\activate
)

echo ===============================
echo 📦 Atualizando o pip...
echo ===============================

python -m pip install --upgrade pip

echo ===============================
echo 📦 Instalando dependências...
echo ===============================

pip install -r requirements.txt

echo ===============================
echo ✅ Configuração concluída com sucesso!
