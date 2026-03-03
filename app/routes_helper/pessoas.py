from app.models.usuarios import Pessoas


def gerar_alias_inicial(nome: str) -> str | None:
    partes = nome.strip().split()

    if len(partes) <= 1:
        return None

    return f"{partes[0]} {partes[-1]}"

def apply_alias(pessoa: Pessoas):
    alias = gerar_alias_inicial(pessoa.nome_pessoa)
    if alias:
        pessoa.alias = alias