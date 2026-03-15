from time import time

from flask import Blueprint, jsonify, render_template

from app.decorators.decorators import admin_required
from app.routes.admin.handlers.handler_admin_meta import (checkout_branch,
                                                          commits_ahead,
                                                          commits_behind,
                                                          create_branch,
                                                          delete_branch,
                                                          get_branch,
                                                          get_commit,
                                                          get_last_commit_info,
                                                          get_local_branches,
                                                          get_remote_branches,
                                                          get_remote_commit,
                                                          git, git_available,
                                                          git_pull,
                                                          has_local_changes,
                                                          last_fetch_time)

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
    
@bp.route("/branches")
@admin_required
def branches():

    return render_template(
        "admin/meta/branches.html",
        local_branches=get_local_branches(),
        remote_branches=get_remote_branches(),
        current=get_branch()
    )

@bp.route("/health")
@admin_required
def health():

    uptime_seconds = int(time() - START_TIME)
    last_fetch = last_fetch_time()

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
                last_fetch.isoformat()
                if last_fetch
                else None
            ),
            "git_installed": git_available()
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

    return jsonify({"out":out, "err": err, "code": code})

@bp.route("/fetch")
@admin_required
def fetch():

    out, err, code = git("fetch")

    return jsonify({"out":out, "err": err, "code": code})
    
@bp.route("/checkout/<branch>")
@admin_required
def checkout(branch):

    out, err, code = checkout_branch(branch)

    return jsonify({"out":out, "err": err, "code": code})

@bp.route("/create_branch")
@admin_required
def create():

    from flask import request

    branch = request.args.get("name")

    if not branch:
        return "Nome da branch não informado"

    out, err, code = create_branch(branch)

    return jsonify({"out":out, "err": err, "code": code})

@bp.route("/delete_branch/<branch>")
@admin_required
def delete(branch):

    out, err, code = delete_branch(branch)

    return jsonify({"out":out, "err": err, "code": code})