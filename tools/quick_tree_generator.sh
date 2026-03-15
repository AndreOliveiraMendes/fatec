#!/usr/bin/env bash

tree --gitignore -a -I '.venv|__pycache__|.git|.vscode|logs|data|.pytest_cache' --dirsfirst "$@"