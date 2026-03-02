def gerar_alias_inicial(nome):
    partes = nome.strip().split()
    return partes[0] if len(partes) == 1 else f"{partes[0]} {partes[-1]}"