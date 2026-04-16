import os
import shutil
import subprocess
from datetime import datetime


def git_available():
    return shutil.which("git") is not None

def git(*args):
    if not git_available():
        return "", "Git não está disponível no servidor.", -1
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def get_branch():
    out, _, _ = git("rev-parse", "--abbrev-ref", "HEAD")
    return out

def get_last_commit_info():
    out, _, _ = git(
        "log",
        "-1",
        "--pretty=format:%h|%an|%ad|%s",
        "--date=iso"
    )

    if not out:
        return None

    h, author, date, msg = out.split("|", 3)

    return {
        "hash": h,
        "author": author,
        "date": date,
        "message": msg
    }

def commits_ahead():
    out, _, _ = git("rev-list", "origin/main..HEAD", "--count")
    try:
        return int(out)
    except:
        return 0

def last_fetch_time():
    path = ".git/FETCH_HEAD"

    if not os.path.exists(path):
        return None

    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts)

def has_local_changes():
    out, _, _ = git("status", "--porcelain")
    return bool(out)

def get_commit():
    out, _, _ = git("rev-parse", "--short", "HEAD")
    return out

def get_remote_commit():
    out, _, _ = git("rev-parse", "--short", "origin/main")
    return out

def commits_behind():
    out, _, _ = git("rev-list", "HEAD..origin/main", "--count")

    try:
        return int(out)
    except:
        return 0

def git_pull():
    return git("pull")

def git_restore():
    return git("restore", ".")

def get_local_branches():
    out, err, code = git("branch")

    if code != 0:
        return []

    branches = []

    for line in out.splitlines():
        line = line.strip()

        if line.startswith("*"):
            branches.append({
                "name": line[2:],
                "current": True
            })
        else:
            branches.append({
                "name": line,
                "current": False
            })

    return branches

def get_remote_branches():
    out, err, code = git("branch", "-r")

    if code != 0:
        return []

    branches = []

    for line in out.splitlines():
        branches.append(line.strip())

    return branches

def git_checkout_branch(branch):
    return git("checkout", branch)

def git_create_branch(branch):
    return git("checkout", "-b", branch)

def git_delete_branch(branch):
    return git("branch", "-D", branch)

def git_fetch_prune():
    return git("fetch", "--prune")