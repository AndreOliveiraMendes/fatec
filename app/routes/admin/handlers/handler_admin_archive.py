import json
import os
from datetime import date, datetime

from sqlalchemy import extract, select

from app.extensions import db
from app.models.aulas import Semestres
from app.models.historicos import Historicos


def archive_last_year_historicos():
    current_year = datetime.now().year
    last_year = current_year - 1

    # 1. Select apenas do ano anterior
    stmt = select(Historicos).where(
        extract('year', Historicos.data_hora) == last_year
    )

    historicos = db.session.execute(stmt).scalars().all()

    if not historicos:
        return "Nada para arquivar."

    # 2. Converter para dict
    data = []
    for h in historicos:
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

    # 3. Salvar JSON
    archive_dir = os.path.join(os.getcwd(), "archive")
    os.makedirs(archive_dir, exist_ok=True)

    filename = f"historicos_{last_year}.json"
    filepath = os.path.join(archive_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # 4. Deletar apenas registros do ano anterior
    db.session.execute(
        Historicos.__table__.delete().where(
            extract('year', Historicos.data_hora) == last_year
        )
    )

    db.session.commit()

    return f"Arquivado {last_year} e removido da tabela."

def archive_by_semestre():
    today = date.today()

    # 1. Buscar semestres já finalizados
    semestres = db.session.execute(
        select(Semestres).where(Semestres.data_fim < today)
    ).scalars().all()

    if not semestres:
        return "Nenhum semestre finalizado."

    archive_dir = os.path.join(os.getcwd(), "archive")
    os.makedirs(archive_dir, exist_ok=True)

    total_arquivados = 0

    for semestre in semestres:
        start = semestre.data_inicio
        end = semestre.data_fim

        # 2. Buscar históricos desse semestre
        historicos = db.session.execute(
            select(Historicos).where(
                Historicos.data_hora >= start,
                Historicos.data_hora <= end
            )
        ).scalars().all()

        if not historicos:
            continue

        # 3. Converter
        data = []
        for h in historicos:
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

        # 4. Nome do arquivo (seguro)
        nome_arquivo = f"historicos_{semestre.nome_semestre.replace(' ', '_')}.json"
        filepath = os.path.join(archive_dir, nome_arquivo)

        # 5. Salvar
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        # 6. Deletar esses registros
        db.session.execute(
            Historicos.__table__.delete().where(
                Historicos.data_hora >= start,
                Historicos.data_hora <= end
            )
        )

        total_arquivados += len(data)

    db.session.commit()

    return f"{total_arquivados} registros arquivados por semestre."