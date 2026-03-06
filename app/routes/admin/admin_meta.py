import subprocess

from flask import Blueprint, render_template
from app.decorators.decorators import admin_required

bp = Blueprint("admin_meta", __name__, url_prefix="/admin/meta")


def git(cmd):
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def has_local_changes():
    out, _, _ = git("git status --porcelain")
    return bool(out)


def get_commit():
    out, _, _ = git("git rev-parse --short HEAD")
    return out


def get_remote_commit():
    git("git fetch")
    out, _, _ = git("git rev-parse --short origin/main")
    return out


def commits_behind():
    git("git fetch")
    out, _, _ = git("git rev-list HEAD..origin/main --count")
    try:
        return int(out)
    except:
        return 0


def git_pull():
    return git("git pull")


@bp.route("/central")
@admin_required
def central():

    local_changes = has_local_changes()
    behind = commits_behind()

    status = {
        "local_commit": get_commit(),
        "remote_commit": get_remote_commit(),
        "behind": behind,
        "local_changes": local_changes
    }

    return render_template("admin/meta/central.html", status=status)


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