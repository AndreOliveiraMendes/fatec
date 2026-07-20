#!/usr/bin/env bash

if ! command -v tree >/dev/null 2>&1; then
    echo "Erro: o comando 'tree' não está instalado." >&2
    exit 127
fi

tree --gitignore -a \
    -I '.venv|__pycache__|.git|.vscode|logs|data|.pytest_cache' \
    --dirsfirst "$@"