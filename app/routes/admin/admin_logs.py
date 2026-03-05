import os
import re
from flask import Blueprint, render_template, request

from app.decorators.decorators import admin_required
from config.mapeamentos import LOG_DIR, MAX_RESULTS

bp = Blueprint("logs", __name__, url_prefix="/admin/logs")

@bp.route("/admin/logs", methods=["GET"])
@admin_required
def logs_view():
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
        files=files,
        results=results,
        summaries=summaries,
        query=query,
        selected_file=selected_file
    )