@echo off
echo ===============================
echo 🐍 Criando ambiente virtual...
echo ===============================

python -m venv .venv

echo ===============================
echo 🔄 Ativando ambiente...
echo ===============================

call .venv\Scripts\activate

echo ===============================
echo 📦 atualizando o pip ...
echo ===============================

python -m pip install --upgrade pip

echo ===============================
echo 📦 Instalando dependências...
echo ===============================

pip install -r requirements.txt