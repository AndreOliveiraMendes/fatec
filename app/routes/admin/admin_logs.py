import os
import re
from flask import Blueprint, render_template, request

from app.decorators.decorators import admin_required
from config.mapeamentos import LOG_DIR, MAX_RESULTS

bp = Blueprint("logs", __name__, url_prefix="/admin/logs")

@bp.route("/admin/logs", methods=["GET"])
@admin_required
def logs_view():
    query = request.args.get("q", "")
    selected_file = request.args.get("file", "")

    files = sorted(
        [f for f in os.listdir(LOG_DIR) if f.startswith("app.log") or f.startswith("commands.log")],
        reverse=True
    )

    results = []

    if query and selected_file:
        filepath = os.path.join(LOG_DIR, selected_file)

        if os.path.exists(filepath):
            regex = re.compile(query, re.IGNORECASE)

            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_number, line in enumerate(f, 1):
                    if regex.search(line):
                        results.append({
                            "line_number": line_number,
                            "content": line.strip()
                        })

                        if len(results) >= MAX_RESULTS:
                            break

    return render_template(
        "admin/logs/logs.html",
        files=files,
        results=results,
        query=query,
        selected_file=selected_file
    )