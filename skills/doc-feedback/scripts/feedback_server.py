#!/usr/bin/env python3
"""Highlight-and-comment feedback GUI for a markdown document.

The browser and the agent never talk directly. They share a session directory:

    DIR/server.json        url/port/pid of the running server
    DIR/pending/<id>.json  highlights waiting for guesses (written by the server)
    DIR/guesses/<id>.json  {"guesses": [...]} (written by the agent)
    DIR/comments.json      saved comments (written by the server)
    DIR/heartbeat          touched by `next` while the agent is listening
    DIR/done               created when the user clicks Finish

Subcommands:
    serve --document PATH --session DIR [--port 8765]
    url   --session DIR [--timeout 15]    print the GUI's URL
    next  --session DIR [--timeout 540]   block until a highlight needs guesses
    stop  --session DIR                   shut the server down

Standard library only.
"""

import argparse
import html
import json
import os
import re
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_lock = threading.Lock()


# --------------------------------------------------------------------------
# Minimal markdown -> HTML. Every top-level block gets data-block="<n>" so the
# UI can store highlight positions as (block, char offset).
# --------------------------------------------------------------------------

# Inline math: $$..$$ and \[..\] are display style, $..$ and \(..\) inline. A
# single $ must hug its content and not touch a word or digit, so "$5 and $10"
# stays text.
MATH_INLINE_RE = re.compile(
    r"\$\$(.+?)\$\$|\\\[(.+?)\\\]|\\\((.+?)\\\)"
    r"|(?<![\\$\w])\$(?![\s$])((?:\\.|[^$\\])+?)(?<![\s\\])\$(?![\w$])"
)
MATH_ENV_RE = re.compile(r"^\s*\\begin\{([A-Za-z]+\*?)\}")


def _math(src, tex, display):
    """A formula the UI typesets with KaTeX. Until then (or offline) it shows `src`."""
    return '<span class="math%s" data-src="%s" data-tex="%s">%s</span>' % (
        " display" if display else "", html.escape(src), html.escape(tex), html.escape(src))


def _inline(text):
    stash = []

    def keep(fragment):
        stash.append(fragment)
        return "\x00%d\x00" % (len(stash) - 1)

    def math(m):
        tex = next(g for g in m.groups() if g is not None)
        return keep(_math(m.group(0), tex.strip(), m.group(1) is not None or m.group(2) is not None))

    text = re.sub(r"`([^`]+)`", lambda m: keep("<code>" + html.escape(m.group(1)) + "</code>"), text)
    text = MATH_INLINE_RE.sub(math, text)
    text = html.escape(text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)", r'<img alt="\1" src="\2">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: "<strong>%s</strong>" % (m.group(1) or m.group(2)), text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", text)
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
    text = text.replace("\\$", "$")
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)


def _is_table_sep(line):
    return bool(re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", line))


def _cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def render_markdown(src):
    lines = src.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out, i, n = [], 0, 0

    def block(tag, inner, attrs=""):
        nonlocal n
        out.append('<%s data-block="%d"%s>%s</%s>' % (tag, n, attrs, inner, tag))
        n += 1

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        fence = re.match(r"^\s*(```|~~~)", line)
        if fence:
            mark, buf = fence.group(1), []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(mark):
                buf.append(lines[i])
                i += 1
            i += 1
            block("pre", "<code>" + html.escape("\n".join(buf)) + "</code>")
            continue
        stripped, env = line.strip(), MATH_ENV_RE.match(line)
        if stripped.startswith(("$$", "\\[")) or env:
            # Display math: $$ .. $$, \[ .. \], or \begin{env} .. \end{env}, possibly multi-line.
            closer = "\\end{%s}" % env.group(1) if env else "$$" if stripped.startswith("$$") else "\\]"
            buf, rest = [stripped], stripped if env else stripped[2:]
            while closer not in rest and i + 1 < len(lines):
                i += 1
                rest = lines[i].strip()
                buf.append(rest)
            i += 1
            src = "\n".join(buf)
            tex = src if env else src[2:].split(closer, 1)[0]
            block("div", _math(src, tex.strip(), True), ' class="math-block"')
            continue
        h = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if h:
            block("h%d" % len(h.group(1)), _inline(h.group(2)))
            i += 1
            continue
        if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        if "|" in line and i + 1 < len(lines) and _is_table_sep(lines[i + 1]):
            head = "".join("<th>%s</th>" % _inline(c) for c in _cells(line))
            rows, i = [], i + 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append("<tr>%s</tr>" % "".join("<td>%s</td>" % _inline(c) for c in _cells(lines[i])))
                i += 1
            block("table", "<thead><tr>%s</tr></thead><tbody>%s</tbody>" % (head, "".join(rows)))
            continue
        if line.lstrip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            block("blockquote", _inline(" ".join(b.strip() for b in buf if b.strip())))
            continue
        lm = re.match(r"^(\s*)([-*+]|\d+[.)])\s+", line)
        if lm:
            ordered = lm.group(2)[0].isdigit()
            items = []
            while i < len(lines):
                m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
                if m:
                    items.append([len(m.group(1)), m.group(3)])
                elif lines[i].strip() and items and lines[i].startswith(" "):
                    items[-1][1] += " " + lines[i].strip()  # continuation line
                else:
                    break
                i += 1
            base = items[0][0]
            lis = "".join(
                '<li%s>%s</li>' % (' class="sub"' if ind > base else "", _inline(t)) for ind, t in items
            )
            block("ol" if ordered else "ul", lis)
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^\s*(#{1,6}\s|```|~~~|>|([-*+]|\d+[.)])\s|\$\$|\\\[|\\begin\{)", lines[i]
        ):
            buf.append(lines[i].strip())
            i += 1
        if not buf:  # safety: unrecognized line, emit as paragraph
            buf, i = [line.strip()], i + 1
        block("p", _inline(" ".join(buf)))
    return "\n".join(out)


# --------------------------------------------------------------------------
# Session storage
# --------------------------------------------------------------------------

def _write_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _read_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


class Session:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.pending = self.root / "pending"
        self.guesses = self.root / "guesses"
        self.comments_path = self.root / "comments.json"
        self.done_path = self.root / "done"
        self.heartbeat = self.root / "heartbeat"
        self.info_path = self.root / "server.json"

    def init(self):
        for d in (self.root, self.pending, self.guesses):
            d.mkdir(parents=True, exist_ok=True)
        if self.done_path.exists():
            self.done_path.unlink()  # reopening a finished session starts a new round

    def comments(self):
        return _read_json(self.comments_path, [])

    def save_comments(self, items):
        _write_json(self.comments_path, items)


# --------------------------------------------------------------------------
# HTTP server
# --------------------------------------------------------------------------

def make_handler(session, doc_path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # keep the agent's background output quiet
            pass

        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _json(self, obj, code=200):
            self._send(code, json.dumps(obj, ensure_ascii=False))

        def _body(self):
            length = int(self.headers.get("Content-Length") or 0)
            try:
                return json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                return {}

        def _id(self, value):
            return value if isinstance(value, str) and ID_RE.match(value) else None

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                self._send(200, (HERE / "ui.html").read_bytes(), "text/html; charset=utf-8")
            elif path == "/doc":
                src = Path(doc_path).read_text(encoding="utf-8")
                self._json({"name": Path(doc_path).name, "html": render_markdown(src)})
            elif path == "/state":
                beat = session.heartbeat.stat().st_mtime if session.heartbeat.exists() else None
                self._json({
                    "comments": session.comments(),
                    "done": session.done_path.exists(),
                    "agent_seconds_ago": None if beat is None else round(time.time() - beat),
                })
            elif path.startswith("/guesses/"):
                hid = self._id(path[len("/guesses/"):])
                if not hid:
                    return self._json({"error": "bad id"}, 400)
                data = _read_json(session.guesses / (hid + ".json"))
                if isinstance(data, dict) and isinstance(data.get("guesses"), list):
                    guesses = [str(g).strip() for g in data["guesses"] if str(g).strip()]
                    self._json({"ready": True, "guesses": guesses})
                else:
                    queued = sorted(p.stat().st_mtime for p in session.pending.glob("*.json")
                                    if not (session.guesses / p.name).exists())
                    mine = session.pending / (hid + ".json")
                    ahead = sum(1 for t in queued if mine.exists() and t < mine.stat().st_mtime)
                    self._json({"ready": False, "ahead": ahead})
            else:
                self._json({"error": "not found"}, 404)

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            body = self._body()
            with _lock:
                if path == "/highlight":
                    hid = self._id(body.get("id"))
                    if not hid or not str(body.get("text", "")).strip():
                        return self._json({"error": "bad highlight"}, 400)
                    rec = {k: body.get(k) for k in ("id", "text", "paragraph", "section")}
                    rec["created"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    _write_json(session.pending / (hid + ".json"), rec)
                    self._json({"ok": True})
                elif path == "/cancel":
                    hid = self._id(body.get("id"))
                    if hid:
                        for p in (session.pending / (hid + ".json"), session.guesses / (hid + ".json")):
                            if p.exists():
                                p.unlink()
                    self._json({"ok": True})
                elif path == "/comment":
                    hid = self._id(body.get("id"))
                    if not hid or not str(body.get("comment", "")).strip():
                        return self._json({"error": "bad comment"}, 400)
                    keys = ("id", "text", "paragraph", "section", "block", "start", "comment",
                            "source", "guess_index", "guesses")
                    rec = {k: body.get(k) for k in keys}
                    now = time.strftime("%Y-%m-%dT%H:%M:%S")
                    items = session.comments()
                    old = next((c for c in items if c.get("id") == hid), None)
                    if old:
                        rec["created"] = old.get("created", now)
                        rec["updated"] = now
                        items = [rec if c.get("id") == hid else c for c in items]
                    else:
                        rec["created"] = now
                        items.append(rec)
                    session.save_comments(items)
                    # A commented highlight no longer needs guesses.
                    p = session.pending / (hid + ".json")
                    if p.exists():
                        p.unlink()
                    self._json({"ok": True})
                elif path == "/comment/delete":
                    hid = self._id(body.get("id"))
                    session.save_comments([c for c in session.comments() if c.get("id") != hid])
                    self._json({"ok": True})
                elif path == "/done":
                    session.done_path.write_text(time.strftime("%Y-%m-%dT%H:%M:%S"), encoding="utf-8")
                    self._json({"ok": True})
                elif path == "/shutdown":
                    self._json({"ok": True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                else:
                    self._json({"error": "not found"}, 404)

    return Handler


def cmd_serve(args):
    doc = Path(args.document).resolve()
    if not doc.is_file():
        sys.exit("document not found: %s" % doc)
    session = Session(args.session)
    session.init()
    server = _bind(args.port, make_handler(session, doc))
    url = "http://127.0.0.1:%d/" % server.server_address[1]
    _write_json(session.info_path, {"url": url, "port": server.server_address[1],
                                    "pid": os.getpid(), "document": str(doc)})
    print("Feedback GUI: %s" % url, flush=True)
    print("Session dir:  %s" % session.root, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if session.info_path.exists():
            session.info_path.unlink()
    print("Server stopped.", flush=True)


# --------------------------------------------------------------------------
# Reaching the GUI. The server may run on a remote host reached through VS Code
# Remote-SSH, often inside tmux, and from here there's no reliable way to tell
# which screen the user is at. So nothing is opened automatically: `url` prints
# a localhost address, which VS Code forwards when the user Ctrl+clicks it.
# --------------------------------------------------------------------------

DEFAULT_PORT = 8765


class _Server(ThreadingHTTPServer):
    allow_reuse_address = os.name != "nt"  # on Windows, SO_REUSEADDR lets two servers share a port


def _bind(port, handler):
    """Bind 127.0.0.1 on `port`, or by default on 8765 or the next free port after it,
    so the address (and any port VS Code forwarded) stays the same across sessions."""
    candidates = [port] if port else list(range(DEFAULT_PORT, DEFAULT_PORT + 20)) + [0]
    for i, p in enumerate(candidates):
        try:
            return _Server(("127.0.0.1", p), handler)
        except OSError:
            if i == len(candidates) - 1:
                raise


def cmd_url(args):
    """Wait for this session's server to answer, then print how to reach it."""
    session = Session(args.session)
    deadline = time.time() + args.timeout
    while True:
        info = _read_json(session.info_path)
        if info:
            try:
                urllib.request.urlopen(info["url"] + "state", timeout=2).read()
                break  # a stale server.json from a crashed run won't answer
            except OSError:
                pass
        if time.time() >= deadline:
            sys.exit("no running server for %s (start `serve` first)" % session.root)
        time.sleep(0.3)
    port = info["port"]
    print(json.dumps({"url": "http://localhost:%d/" % port, "port": port}, indent=2))


# --------------------------------------------------------------------------
# Agent-side commands
# --------------------------------------------------------------------------

def cmd_next(args):
    session = Session(args.session)
    if not session.pending.is_dir():
        sys.exit("no session at %s (start `serve` first)" % session.root)
    deadline = time.time() + args.timeout
    while True:
        session.heartbeat.write_text(str(time.time()), encoding="utf-8")
        if session.done_path.exists():
            print(json.dumps({"done": True, "comments_path": str(session.comments_path)}))
            return
        waiting = sorted(
            (p for p in session.pending.glob("*.json") if not (session.guesses / p.name).exists()),
            key=lambda p: p.stat().st_mtime,
        )
        for p in waiting:
            rec = _read_json(p)
            if rec is None:
                continue  # half-written; pick it up next round
            prior = [{"text": c.get("text"), "comment": c.get("comment"), "source": c.get("source")}
                     for c in session.comments()]
            rec["guesses_path"] = str(session.guesses / p.name)
            rec["queue_remaining"] = len(waiting) - 1
            rec["prior_comments"] = prior
            print(json.dumps(rec, ensure_ascii=False, indent=2))
            return
        if time.time() >= deadline:
            print(json.dumps({"idle": True}))
            return
        time.sleep(0.3)


def cmd_stop(args):
    info = _read_json(Session(args.session).info_path)
    if not info:
        print("No running server recorded for this session.")
        return
    try:
        req = urllib.request.Request(info["url"] + "shutdown", data=b"{}", method="POST",
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5).read()
        print("Stopped server at %s" % info["url"])
    except OSError as e:
        print("Could not reach server (%s); it may already be stopped." % e)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="start the feedback GUI")
    s.add_argument("--document", required=True)
    s.add_argument("--session", required=True)
    s.add_argument("--port", type=int, default=0, help="default: 8765 or the next free port")
    u = sub.add_parser("url", help="print the GUI's URL once the server answers")
    u.add_argument("--session", required=True)
    u.add_argument("--timeout", type=float, default=15)
    nx = sub.add_parser("next", help="wait for the next highlight that needs guesses")
    nx.add_argument("--session", required=True)
    nx.add_argument("--timeout", type=float, default=540)
    st = sub.add_parser("stop", help="stop the server")
    st.add_argument("--session", required=True)
    args = ap.parse_args()
    {"serve": cmd_serve, "url": cmd_url, "next": cmd_next, "stop": cmd_stop}[args.cmd](args)


if __name__ == "__main__":
    main()
