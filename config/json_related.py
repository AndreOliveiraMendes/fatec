import importlib.resources as resources
import json
from importlib.resources import as_file
from pathlib import Path

from config.mapeamentos import (COMMANDS_FILE, DEFAULT_CONFIG_CFG,
                                DEFAULT_PAINEL_CFG, SSH_CRED_FILE)


def validar_json(data, *args):
    for field in args:
        if not field in data:
            return False
    return True

def carregar_painel_config():
    resource = resources.files("config").joinpath("painel.json")

    # pegar um Path real (mesmo se for empacotado)
    with as_file(resource) as painel_path:
        painel_file = Path(painel_path)

        if not painel_file.exists() or painel_file.stat().st_size == 0:
            # cria o arquivo com config padrão
            painel_file.write_text(json.dumps(DEFAULT_PAINEL_CFG, indent=4, ensure_ascii=False), encoding="utf-8")
            return DEFAULT_PAINEL_CFG

        try:
            data = json.loads(painel_file.read_text(encoding="utf-8").strip() or "{}")
            if not validar_json(data, 'tipo', 'tempo', 'laboratorios'):
                raise ValueError("JSON não contém os campos obrigatórios.")
            return data
        except (json.JSONDecodeError, ValueError):
            # reescreve com padrão se estiver corrompido
            painel_file.write_text(json.dumps(DEFAULT_PAINEL_CFG, indent=4, ensure_ascii=False), encoding="utf-8")
            return DEFAULT_PAINEL_CFG

def carregar_config_geral():
    resource = resources.files("config").joinpath("config.json")

    with as_file(resource) as config_path:
        config_file = Path(config_path)

        if not config_file.exists() or config_file.stat().st_size == 0:
            config_file.write_text(json.dumps(DEFAULT_CONFIG_CFG, indent=4, ensure_ascii=False), encoding="utf-8")
            return DEFAULT_CONFIG_CFG

        try:
            data = json.loads(config_file.read_text(encoding="utf-8").strip() or "{}")
            if not validar_json(data, 'modo_gerenciacao', 'toleranca'):
                raise ValueError("JSON não contém os campos obrigatórios.")
            return data
        except (json.JSONDecodeError, ValueError):
            # reescreve com padrão se estiver corrompido
            config_file.write_text(json.dumps(DEFAULT_CONFIG_CFG, indent=4, ensure_ascii=False), encoding="utf-8")
            return DEFAULT_CONFIG_CFG

def load_ssh_credentials():
    if SSH_CRED_FILE.exists():
        with SSH_CRED_FILE.open("r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_ssh_credentials(creds):
    SSH_CRED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SSH_CRED_FILE.open("w", encoding="utf-8") as f:
        json.dump(creds, f, ensure_ascii=False, indent=4)

def load_commands():
    if COMMANDS_FILE.exists():
        with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_commands(commands):
    COMMANDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with COMMANDS_FILE.open("w", encoding="utf-8") as f:
        json.dump(commands, f, ensure_ascii=False, indent=4)