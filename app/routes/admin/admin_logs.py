import os
import re

from flask import Blueprint, Response, render_template, request, session
from sqlalchemy import distinct, func, select

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.extensions import db
from app.models.historicos import Historicos
from app.models.usuarios import Pessoas, Usuarios
from app.routes.admin.handlers.handler_admin_logs import apply_log_filters
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

@bp.route("/admin/logs/db", methods=["GET"])
@admin_required
def logs_db():
    user = get_user(session.get('userid'))
    tabela_selecionada = request.args.get("tabela")
    categoria_selecionada = request.args.get("categoria")

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
    )

    # Aplica filtros
    stmt = apply_log_filters(stmt)

    logs = db.session.execute(stmt).all()

    return render_template(
        "admin/logs/logs_db.html",
        user=user,
        logs=logs,
        tabelas=distinct_tabelas,
        tabela_selecionada=tabela_selecionada,
        categorias=distinct_categorias,
        categoria_selecionada=categoria_selecionada
    )

@bp.route("/metrics", methods=["GET"])
@admin_required
def logs_metrics():
    user = get_user(session.get('userid'))

    # =========================
    # BASE QUERY (reutilizável)
    # =========================
    base_stmt = select(Historicos)
    base_stmt = apply_log_filters(base_stmt)

    base_subq = base_stmt.subquery()

    # =========================
    # 📅 LOGS POR DIA
    # =========================
    logs_por_dia_stmt = (
        select(
            func.date(base_subq.c.data_hora).label("dia"),
            func.count().label("total")
        )
        .group_by(func.date(base_subq.c.data_hora))
        .order_by(func.date(base_subq.c.data_hora))
    )

    logs_por_dia = db.session.execute(logs_por_dia_stmt).all()

    # =========================
    # 📊 MÉDIA POR DIA
    # =========================
    sub_media = (
        select(
            func.date(base_subq.c.data_hora).label("dia"),
            func.count().label("total")
        )
        .group_by(func.date(base_subq.c.data_hora))
    ).subquery()

    resumo = db.session.execute(
        select(func.avg(sub_media.c.total).label('media'), func.sum(sub_media.c.total).label('total'))
    ).first()

    total_geral = db.session.execute(
        select(func.count()).select_from(base_subq)
    ).scalar()

    # =========================
    # 📂 POR TABELA
    # =========================
    por_tabela_stmt = (
        select(
            base_subq.c.tabela,
            func.count().label("total")
        )
        .group_by(base_subq.c.tabela)
        .order_by(func.count().desc())
    )

    por_tabela = [
        (tabela, total, (total / total_geral * 100) if total_geral else 0)
        for tabela, total in db.session.execute(por_tabela_stmt)
    ]


    # =========================
    # 🏷 POR CATEGORIA
    # =========================
    por_categoria_stmt = (
        select(
            base_subq.c.categoria,
            func.count().label("total")
        )
        .group_by(base_subq.c.categoria)
        .order_by(func.count().desc())
    )

    por_categoria = [
        (categoria, total, (total / total_geral * 100) if total_geral else 0)
        for categoria, total in db.session.execute(por_categoria_stmt)
    ]

    return render_template(
        "admin/logs/metrics.html",
        user=user,
        logs_por_dia=logs_por_dia,
        resumo=resumo,
        por_tabela=por_tabela,
        por_categoria=por_categoria,
    )

@bp.route("/export")
@admin_required
def export_logs():

    def generate():
        yield "id,data_hora,tabela,categoria,message\n"

        stmt = select(Historicos).order_by(Historicos.data_hora)

        for row in db.session.execute(stmt).scalars():
            yield f"{row.id_historico},{row.data_hora},{row.tabela},{row.categoria},{row.message}\n"

    return Response(generate(), mimetype="text/csv")