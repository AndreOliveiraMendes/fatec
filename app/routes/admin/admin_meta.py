import sys
from time import time
import platform

from flask import Blueprint, jsonify, render_template
from app.decorators.decorators import admin_required
from app.routes.admin.handlers.handler_admin_meta import commits_ahead, commits_behind, get_branch, get_commit, get_last_commit_info, get_remote_commit, git, git_pull, has_local_changes, last_fetch_time

bp = Blueprint("admin_meta", __name__, url_prefix="/admin/meta")
START_TIME = time()

@bp.route("/central")
@admin_required
def central():

    local_changes = has_local_changes()

    status = {
        "branch": get_branch(),
        "local_commit": get_commit(),
        "remote_commit": get_remote_commit(),
        "behind": commits_behind(),
        "ahead": commits_ahead(),
        "local_changes": local_changes,
        "last_fetch": last_fetch_time(),
        "last_commit": get_last_commit_info()
    }

    return render_template(
        "admin/meta/central.html",
        status=status
    )

@bp.route("/health")
@admin_required
def health():

    uptime_seconds = int(time() - START_TIME)

    status = {
        "status": "ok",
        "git": {
            "branch": get_branch(),
            "local_commit": get_commit(),
            "remote_commit": get_remote_commit(),
            "ahead": commits_ahead(),
            "behind": commits_behind(),
            "local_changes": has_local_changes(),
            "last_fetch": (
                last_fetch_time().isoformat()
                if last_fetch_time()
                else None
            )
        },
        "server": {
            "python_version": "3.12",
            "os": "Linux-6.6-Ubuntu",
            "hostname": "srv-prod-01",
            "uptime_seconds": uptime_seconds
        }
    }

    return jsonify(status)

@bp.route("/update")
@admin_required
def update():

    if has_local_changes():
        return "Existem alterações locais. Update bloqueado."

    behind = commits_behind()

    if behind == 0:
        return "Sistema já está atualizado."

    out, err, code = git_pull()

    return f"<pre>{out}</pre>"

@bp.route("/fetch")
@admin_required
def fetch():

    out, err, code = git("fetch")

    return jsonify({"out":out, "err": err, "code": code})