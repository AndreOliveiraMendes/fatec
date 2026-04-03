import json
import os
from datetime import date, datetime, time

from sqlalchemy import delete, extract, select

from app.extensions import db
from app.models.aulas import Semestres
from app.models.historicos import Historicos


def save_historicos(data, tipo, periodo):
    base_dir = os.path.join(os.getcwd(), "archive")
    if tipo == "ano":
        path = os.path.join(base_dir, "anos")
    else:
        path = os.path.join(base_dir, "semestres")
    os.makedirs(path, exist_ok=True)
    filename = f"historicos_{periodo}.json"
    filepath = os.path.join(path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return filepath

def archive_last_year_historicos():
    current_year = datetime.now().year
    last_year = current_year - 1

    stmt = select(Historicos).where(
        extract('year', Historicos.data_hora) == last_year
    )

    result = db.session.execute(stmt).scalars()

    data = []
    count = 0

    for h in result:
        data.append({
            "id_historico": h.id_historico,
            "id_usuario": h.id_usuario,
            "tabela": h.tabela,
            "categoria": h.categoria,
            "data_hora": h.data_hora.isoformat(),
            "message": h.message,
            "chave_primaria": h.chave_primaria,
            "observacao": h.observacao,
            "origem": h.origem
        })
        count += 1

    if count == 0:
        return "Nada para arquivar."

    archive_dir = os.path.join(os.getcwd(), "archive")
    os.makedirs(archive_dir, exist_ok=True)

    save_historicos(data, "ano", last_year)

    # DELETE moderno
    db.session.execute(
        delete(Historicos).where(
            extract('year', Historicos.data_hora) == last_year
        )
    )

    db.session.commit()

    return f"{count} registros do ano {last_year} arquivados."

def archive_by_semestre():
    today = date.today()

    semestres = db.session.execute(
        select(Semestres).where(Semestres.data_fim < today)
    ).scalars().all()

    if not semestres:
        return "Nenhum semestre finalizado."

    archive_dir = os.path.join(os.getcwd(), "archive")
    os.makedirs(archive_dir, exist_ok=True)

    total_arquivados = 0

    for semestre in semestres:
        start_dt = datetime.combine(semestre.data_inicio, time.min)
        end_dt = datetime.combine(semestre.data_fim, time.max)

        stmt = select(Historicos).where(
            Historicos.data_hora >= start_dt,
            Historicos.data_hora <= end_dt
        )

        result = db.session.execute(stmt).scalars()

        data = []
        count = 0

        for h in result:
            data.append({
                "id_historico": h.id_historico,
                "id_usuario": h.id_usuario,
                "tabela": h.tabela,
                "categoria": h.categoria,
                "data_hora": h.data_hora.isoformat(),
                "message": h.message,
                "chave_primaria": h.chave_primaria,
                "observacao": h.observacao,
                "origem": h.origem
            })
            count += 1

        if count == 0:
            continue

        save_historicos(data, "semestre", periodo=semestre.nome_semestre.replace(' ', '_'))

        # DELETE moderno
        db.session.execute(
            delete(Historicos).where(
                Historicos.data_hora >= start_dt,
                Historicos.data_hora <= end_dt
            )
        )

        total_arquivados += count

    db.session.commit()

    return f"{total_arquivados} registros arquivados por semestre."

def preview_last_year():
    current_year = datetime.now().year
    last_year = current_year - 1

    count = db.session.execute(
        select(Historicos).where(
            extract('year', Historicos.data_hora) == last_year
        )
    ).scalars().all()

    total = len(count)

    return f"Ano: {last_year}\nRegistros encontrados: {total}"

def preview_semestre():
    today = date.today()

    semestres = db.session.execute(
        select(Semestres).where(Semestres.data_fim < today)
    ).scalars().all()

    total = 0
    detalhes = []

    for s in semestres:
        count = db.session.execute(
            select(Historicos).where(
                Historicos.data_hora >= s.data_inicio,
                Historicos.data_hora <= s.data_fim
            )
        ).scalars().all()

        qtd = len(count)

        if qtd > 0:
            detalhes.append(f"{s.nome_semestre}: {qtd}")
            total += qtd

    if total == 0:
        return "Nenhum dado para arquivar."

    return "Total: {}\n\n{}".format(total, "\n".join(detalhes))