def resolver_reserva(temp, fixa, exibicao):
    choose = temp or fixa

    tipo = (
        "temporaria" if temp
        else "fixa" if fixa
        else "neither"
    )

    if exibicao:
        choose = {"fixa": fixa, "temporaria": temp}.get(
            exibicao.tipo_reserva.value,
            choose
        )

        tipo = {
            "fixa": "fixa",
            "temporaria": "temporaria"
        }.get(
            exibicao.tipo_reserva.value,
            tipo
        )

    return choose, tipo