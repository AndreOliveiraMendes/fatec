from datetime import datetime
import os
import subprocess

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

def git(*args):
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

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
    git("fetch")
    out, _, _ = git("rev-list", "HEAD..origin/main", "--count")

    try:
        return int(out)
    except:
        return 0

def git_pull():
    return git("pull")