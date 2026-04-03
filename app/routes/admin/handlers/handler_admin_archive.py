import json
import os
import zipfile
from datetime import date, datetime, time
from io import BytesIO

from flask import abort, send_file
from sqlalchemy import delete, extract, func, select

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

def archive_all_previous_years():
    current_year = datetime.now().year
    last_year = current_year - 1

    min_year = db.session.execute(
        select(func.min(extract('year', Historicos.data_hora)))
    ).scalar()

    if not min_year:
        return "Nenhum registro encontrado."

    total_arquivados = 0

    for year in range(int(min_year), last_year + 1):
        stmt = select(Historicos).where(
            extract('year', Historicos.data_hora) == year
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

        # salva no lugar certo
        save_historicos(data, "ano", year)

        # deleta
        db.session.execute(
            delete(Historicos).where(
                extract('year', Historicos.data_hora) == year
            )
        )

        total_arquivados += count

    db.session.commit()

    return f"{total_arquivados} registros arquivados (anos até {last_year})."

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

def preview_all_previous_years():
    current_year = datetime.now().year
    last_year = current_year - 1

    # menor ano existente
    min_year = db.session.execute(
        select(func.min(extract('year', Historicos.data_hora)))
    ).scalar()

    if not min_year:
        return "Nenhum registro encontrado."

    linhas = []
    total_geral = 0

    for year in range(int(min_year), last_year + 1):
        count = db.session.execute(
            select(func.count()).where(
                extract('year', Historicos.data_hora) == year
            )
        ).scalar()
        
        count = int(count) if count else 0

        if count > 0:
            linhas.append(f"{year}: {count} registros")
            total_geral += count

    if total_geral == 0:
        return "Nada para arquivar."

    preview = "Arquivamento por ano:\n\n"
    preview += "\n".join(linhas)
    preview += f"\n\nTotal: {total_geral}"

    return preview

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

def list_archives_files():
    archive_path = os.path.join(os.getcwd(), "archive")
    arquivos = {
        "anos": [],
        "semestres": []
    }
    for tipo in arquivos.keys():
        tipo_path = os.path.join(archive_path, tipo)
        if os.path.exists(tipo_path):
            for filename in os.listdir(tipo_path):
                if filename.endswith(".json"):
                    arquivos[tipo].append(filename)
    return arquivos

def download_archive(tipo=None, file=None):
    archive_path = os.path.join(os.getcwd(), "archive")

    # 🔒 tipos permitidos
    allowed_tipos = {"anos", "semestres"}

    # ==============================
    # 📄 BAIXAR ARQUIVO ESPECÍFICO
    # ==============================
    if tipo and file:
        if tipo not in allowed_tipos:
            abort(400, description="Tipo inválido.")

        safe_name = os.path.basename(file)  # evita ../
        file_path = os.path.join(archive_path, tipo, safe_name)

        if not os.path.exists(file_path):
            abort(404, description="Arquivo não encontrado.")

        return send_file(file_path, as_attachment=True)

    # ==============================
    # 📁 ZIPAR UM TIPO
    # ==============================
    if tipo:
        if tipo not in allowed_tipos:
            abort(400, description="Tipo inválido.")

        target_path = os.path.join(archive_path, tipo)

        arquivos = []

        for root, dirs, files in os.walk(target_path):
            for f in files:
                if f.endswith(".json"):
                    full_path = os.path.join(root, f)
                    arcname = os.path.relpath(full_path, archive_path)
                    arquivos.append((full_path, arcname))

        if not arquivos:
            abort(404, description="Nenhum arquivo para download.")

        memory_file = BytesIO()

        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for full_path, arcname in arquivos:
                zf.write(full_path, arcname)

        memory_file.seek(0)

        return send_file(
            memory_file,
            download_name=f"{tipo}.zip",
            as_attachment=True
        )

    # ==============================
    # 🧳 ZIPAR TUDO
    # ==============================
    arquivos = []

    for root, dirs, files in os.walk(archive_path):
        for f in files:
            if f.endswith(".json"):
                full_path = os.path.join(root, f)
                arcname = os.path.relpath(full_path, archive_path)
                arquivos.append((full_path, arcname))

    if not arquivos:
        abort(404, description="Nenhum arquivo no archive.")

    memory_file = BytesIO()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for full_path, arcname in arquivos:
            zf.write(full_path, arcname)

    memory_file.seek(0)

    return send_file(
        memory_file,
        download_name="archive.zip",
        as_attachment=True
    )