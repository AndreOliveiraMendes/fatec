@echo off
setlocal enabledelayedexpansion

echo ===============================
echo 🔧 Verificando .vscode...
echo ===============================

if not exist ".vscode" (
    echo 📁 Criando pasta .vscode
    mkdir .vscode
) else (
    echo 📁 Pasta .vscode já existe
)

echo ===============================
echo 🔎 Verificando .vscode/settings.json...
echo ===============================

if exist ".vscode\settings.json" (
    echo ⚠️  O arquivo settings.json já existe.
    echo Ele será substituído com as configurações desejadas!
) else (
    echo ✅ Arquivo settings.json não encontrado. Será criado!
)

echo ===============================
echo 📝 Escrevendo configurações...
echo ===============================

(
    echo {
    echo     "files.associations": {
    echo         "base*": "jinja-html",
    echo         "*.jinja": "jinja-html",
    echo         "*.html": "jinja-html"
    echo     },
    echo     "editor.tabSize": 4,
    echo     "editor.insertSpaces": true,
    echo     "files.eol": "\n"
    echo }
) > ".vscode\settings.json"

echo ===============================
echo ✅ Configuração concluída!
