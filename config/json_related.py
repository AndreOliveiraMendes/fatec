import importlib.resources as resources
import json
from importlib.resources import as_file
from pathlib import Path

DEFAULT_PAINEL_CFG = {
    "tipo": "Aula",
    "tempo": "15",
    "laboratorios": "6"
}

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
            return json.loads(painel_file.read_text(encoding="utf-8").strip() or "{}")
        except json.JSONDecodeError:
            # reescreve com padrão se estiver corrompido
            painel_file.write_text(json.dumps(DEFAULT_PAINEL_CFG, indent=4, ensure_ascii=False), encoding="utf-8")
            return DEFAULT_PAINEL_CFG