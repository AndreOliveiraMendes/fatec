#!/usr/bin/env bash

if ! output=$(./quick_tree_generator.sh "$@" > structure.txt 2>&1); then
    echo "Falha ao gerar a estrutura:"
    echo "$output"
    exit 1
fi