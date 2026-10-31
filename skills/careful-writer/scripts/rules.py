#!/usr/bin/env python3
"""Fetch the user's writing rules from the latest commit of a GitHub repository, or push a
change to one rule file.

The repository is named by --repo or the WRITING_RULES_REPO environment variable
("owner/name"). Its index.md holds a table whose rows name a rule file in backticks and say
when to read it.

  rules.py fetch [--repo OWNER/NAME]
      Resolves the latest commit on main, downloads index.md and every file it lists at that
      commit into a local cache, and prints JSON: source ("live", or "cache" when GitHub could
      not be reached, or "none" when no repository is configured), repo, commit, fetched_at,
      dir, and files (path, local, when, blob). A file's "blob" is what push needs as --base.

  rules.py push --path FILE --file LOCAL --base BLOB --message MSG [--repo OWNER/NAME]
      Replaces FILE on main with the contents of LOCAL, only if FILE is still at blob BASE.
      Prints JSON: pushed (true, with commit) or conflict (true, when FILE changed since it was
      read: fetch again, merge, and push with the new blob).

Reads use the GitHub CLI (gh) when it is installed and signed in, and the public API
otherwise. Pushes need gh. Standard library only.
"""
import argparse
import base64
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "write-better", "rules")


class Unreachable(Exception):
    pass


def have_gh():
    if not shutil.which("gh"):
        return False
    return subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0


def api_get(route, gh):
    if gh:
        r = subprocess.run(["gh", "api", route], capture_output=True)
        if r.returncode != 0:
            err = r.stderr.decode("utf-8", "replace").strip()
            if "HTTP 404" in err:
                raise SystemExit(f"{route}: not found on GitHub")
            raise Unreachable(err)
        return json.loads(r.stdout)
    req = urllib.request.Request(f"{API}/{route}", headers={"Accept": "application/vnd.github+json",
                                                            "User-Agent": "write-better"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise SystemExit(f"{route}: not found on GitHub")
        raise Unreachable(str(e))
    except (urllib.error.URLError, OSError) as e:
        raise Unreachable(str(e))


def get_file(repo, path, commit, gh):
    d = api_get(f"repos/{repo}/contents/{path}?ref={commit}", gh)
    return base64.b64decode(d["content"]), d["sha"]


def parse_index(text):
    rows = []
    for line in text.splitlines():
        m = re.match(r"\|\s*`([^`]+\.md)`\s*\|(.*)\|\s*$", line)
        if m:
            rows.append((m.group(1), m.group(2).strip()))
    return rows


def cache_dir(repo):
    return os.path.join(CACHE, repo.replace("/", "__"))


def fetch(repo):
    gh = have_gh()
    out = cache_dir(repo)
    commit = api_get(f"repos/{repo}/commits/main", gh)["sha"]
    index, index_blob = get_file(repo, "index.md", commit, gh)
    rows = parse_index(index.decode("utf-8"))
    if not rows:
        raise SystemExit(f"{repo}: index.md lists no rule files")
    tmp = out + ".new"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    files = [{"path": "index.md", "when": "manifest", "blob": index_blob}]
    open(os.path.join(tmp, "index.md"), "wb").write(index)
    for path, when in rows:
        data, blob = get_file(repo, path, commit, gh)
        os.makedirs(os.path.dirname(os.path.join(tmp, path)) or tmp, exist_ok=True)
        open(os.path.join(tmp, path), "wb").write(data)
        files.append({"path": path, "when": when, "blob": blob})
    meta = {"repo": repo, "commit": commit,
            "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "files": files}
    json.dump(meta, open(os.path.join(tmp, "meta.json"), "w"), indent=1)
    shutil.rmtree(out, ignore_errors=True)
    os.replace(tmp, out)
    return meta


def report(meta, source, note=None):
    d = cache_dir(meta["repo"])
    res = {"source": source, "repo": meta["repo"], "commit": meta["commit"],
           "fetched_at": meta["fetched_at"], "dir": d,
           "files": [dict(f, local=os.path.join(d, f["path"])) for f in meta["files"]]}
    if note:
        res["note"] = note
    print(json.dumps(res, indent=1))


def cmd_fetch(a):
    repo = a.repo or os.environ.get("WRITING_RULES_REPO")
    if not repo:
        print(json.dumps({"source": "none"}))
        return
    try:
        report(fetch(repo), "live")
    except Unreachable as e:
        meta_path = os.path.join(cache_dir(repo), "meta.json")
        if not os.path.exists(meta_path):
            raise SystemExit(f"cannot reach GitHub and no cached rules for {repo}: {e}")
        report(json.load(open(meta_path)), "cache", f"GitHub unreachable ({e}); using the cached copy")


def cmd_push(a):
    repo = a.repo or os.environ.get("WRITING_RULES_REPO")
    if not repo:
        raise SystemExit("no rules repository: pass --repo or set WRITING_RULES_REPO")
    if not have_gh():
        raise SystemExit("pushing needs the GitHub CLI (gh), signed in")
    body = {"message": a.message, "branch": "main", "sha": a.base,
            "content": base64.b64encode(open(a.file, "rb").read()).decode()}
    r = subprocess.run(["gh", "api", "-X", "PUT", f"repos/{repo}/contents/{a.path}", "--input", "-"],
                       input=json.dumps(body).encode(), capture_output=True)
    if r.returncode == 0:
        d = json.loads(r.stdout)
        print(json.dumps({"pushed": True, "commit": d["commit"]["sha"], "blob": d["content"]["sha"]}))
        return
    err = (r.stdout + r.stderr).decode("utf-8", "replace")
    if "409" in err or "does not match" in err:
        print(json.dumps({"conflict": True, "path": a.path,
                          "note": "the file changed on main since it was read: fetch, merge, confirm, push again"}))
        return
    raise SystemExit(err.strip())


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--repo")
    f.set_defaults(fn=cmd_fetch)
    u = sub.add_parser("push")
    u.add_argument("--repo")
    u.add_argument("--path", required=True)
    u.add_argument("--file", required=True)
    u.add_argument("--base", required=True)
    u.add_argument("--message", required=True)
    u.set_defaults(fn=cmd_push)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
