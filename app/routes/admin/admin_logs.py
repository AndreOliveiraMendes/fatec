import os
import re
from datetime import datetime

from flask import Blueprint, render_template, request, session
from sqlalchemy import func, select

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.extensions import db
from app.models.historicos import Historicos
from app.models.usuarios import Pessoas, Usuarios
from config.mapeamentos import LOG_DIR, MAX_RESULTS

bp = Blueprint("logs", __name__, url_prefix="/admin/logs")

@bp.route("/admin/logs", methods=["GET"])
@admin_required
def logs_view():
    user = get_user(session.get('userid'))
    query = request.args.get("q", "").strip()
    selected_file = request.args.get("file", "").strip()

    files = sorted(
        [f for f in os.listdir(LOG_DIR)
         if f.startswith("app.log") or f.startswith("commands.log")],
        reverse=True
    )

    results = []
    summaries = []

    # ==============================
    # 🔎 CASO 1: Busca com query
    # ==============================
    if query:
        regex = re.compile(query, re.IGNORECASE)

        search_files = [selected_file] if selected_file else files

        for filename in search_files:
            filepath = os.path.join(LOG_DIR, filename)

            if not os.path.exists(filepath):
                continue

            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_number, line in enumerate(f, 1):
                    if regex.search(line):
                        results.append({
                            "file": filename,
                            "line_number": line_number,
                            "content": line.strip()
                        })

                        if len(results) >= MAX_RESULTS:
                            break

            if len(results) >= MAX_RESULTS:
                break

    # ==============================
    # 📊 CASO 2: Sem query → resumo
    # ==============================
    else:
        for filename in files:
            filepath = os.path.join(LOG_DIR, filename)

            if not os.path.exists(filepath):
                continue

            info = warning = error = total = 0

            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    total += 1
                    if "ERROR" in line:
                        error += 1
                    elif "WARNING" in line:
                        warning += 1
                    elif "INFO" in line:
                        info += 1

            size_kb = round(os.path.getsize(filepath) / 1024, 2)

            summaries.append({
                "file": filename,
                "total": total,
                "info": info,
                "warning": warning,
                "error": error,
                "size_kb": size_kb
            })

    return render_template(
        "admin/logs/logs.html",
        user=user,
        files=files,
        results=results,
        summaries=summaries,
        query=query,
        selected_file=selected_file
    )
    
from datetime import datetime

from sqlalchemy import distinct, func, select


@bp.route("/admin/logs/db", methods=["GET"])
@admin_required
def logs_db():
    # filtros do request
    tabela_selecionada = request.args.get("tabela")
    categoria_selecionada = request.args.get("categoria")
    q = request.args.get("q")
    origem = request.args.get("origem")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    # GET DISTINCT tabelas
    distinct_tabelas = db.session.execute(
        select(distinct(Historicos.tabela)).order_by(Historicos.tabela)
    ).scalars().all()

    # GET DISTINCT categorias
    distinct_categorias = db.session.execute(
        select(distinct(Historicos.categoria)).order_by(Historicos.categoria)
    ).scalars().all()

    # Query dos logs com LEFT JOIN para usuário/pessoa
    stmt = (
        select(
            Historicos,
            func.coalesce(Pessoas.nome_pessoa, "Sistema").label("nome_pessoa")
        )
        .join(Usuarios, Historicos.id_usuario == Usuarios.id_usuario, isouter=True)
        .join(Pessoas, Usuarios.id_pessoa == Pessoas.id_pessoa, isouter=True)
        .order_by(Historicos.data_hora.desc())
        .limit(200)
    )

    # Aplica filtros
    if tabela_selecionada:
        stmt = stmt.where(Historicos.tabela == tabela_selecionada)
    if categoria_selecionada:
        stmt = stmt.where(Historicos.categoria == categoria_selecionada)
    if q:
        stmt = stmt.where(Historicos.message.ilike(f"%{q}%"))
    if origem:
        stmt = stmt.where(Historicos.origem == origem)
    if data_inicio:
        stmt = stmt.where(Historicos.data_hora >= datetime.fromisoformat(data_inicio))
    if data_fim:
        stmt = stmt.where(Historicos.data_hora <= datetime.fromisoformat(data_fim))

    logs = db.session.execute(stmt).all()

    return render_template(
        "admin/logs/logs_db.html",
        logs=logs,
        tabelas=distinct_tabelas,
        tabela_selecionada=tabela_selecionada,
        categorias=distinct_categorias,
        categoria_selecionada=categoria_selecionada
    )