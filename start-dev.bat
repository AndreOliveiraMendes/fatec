@echo off
echo ===============================
echo 🔧 Configurando Git...
echo ===============================

git config --global user.name "%GIT_USER_NAME%"
git config --global user.email "%GIT_USER_EMAIL%"
git config --global credential.helper manager-core

echo ===============================
echo 🐍 Criando ambiente virtual...
echo ===============================

python -m venv .venv

echo ===============================
echo 📁 Ignorando arquivos do .venv...
echo ===============================

if not exist ".venv\.gitignore" (
    echo * > .venv\.gitignore
    echo Criado: .venv\.gitignore
) else (
    echo .venv\.gitignore já existe.
)

echo ===============================
echo 🔄 Ativando ambiente...
echo ===============================

call .venv\Scripts\activate

echo ===============================
echo 📦 Atualizando o pip...
echo ===============================

python -m pip install --upgrade pip

echo ===============================
echo 📦 Instalando dependências...
echo ===============================

pip install -r requirements.txt
