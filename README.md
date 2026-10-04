# write-better

A Claude Code plugin with two skills that share one writing-style file. Each skill works on its own; together they form a loop where every round of feedback makes the next piece better.

| Skill | What it does |
|---|---|
| `careful-writer` | Makes the agent write like a careful human writer instead of in one shot, for any prose that matters: reports, papers, proposals, docs, emails, statements, or a rewrite of existing text. It outlines first, then drafts **one sentence at a time** on disk. After each sentence it re-reads the paragraph, after each paragraph the section, and after each section the whole piece, revising each time against your style file. It ends with a fresh-reader subagent pass and a rule-by-rule style check. |
| `doc-feedback` | Serves a browser GUI, at a URL you open, on any document (converted to markdown if needed). You highlight words or sentences, and the agent guesses your comment live in a drop-down: technical points (correctness, derivations, methods, missing results) as well as writing. Each guess can be edited, and the last row is always "write my own". When you finish, the agent proposes fixes to the document, plus new or updated rules for your style file for writing preferences that carry over. Technical feedback on one document never goes into the style file, and rules are written only after you confirm. |

## Install

In Claude Code:

```
/plugin marketplace add yoshi74ls181/write-better
/plugin install write-better@write-better
```

The first command registers this repo as a plugin marketplace; the second installs the plugin from it. To work from a local clone instead, pass its path to `/plugin marketplace add`.

Requirements: Python 3.8+ (standard library only) and any modern browser. Math typesetting needs internet access for KaTeX.

## The style file

Both skills use `~/.claude/writing-style.md` by default. To use a different file, set `WRITING_STYLE_FILE` or name a path in your request. The format is described in `skills/doc-feedback/references/style-file-format.md`. Until the file exists, `careful-writer` falls back to `skills/careful-writer/references/default-style.md`.

## Typical use

1. Ask for a piece of writing, e.g. "Investigate X and write a report" or "Draft the related-work section." `careful-writer` triggers on writing tasks; you can also ask for it by name.
2. Say "let me give feedback on this", or name a file, or run `/doc-feedback`. The agent prints a URL; open it (Ctrl+click works in most terminals, including VS Code's).
3. Select text. A popover shows "Guessing your comment…". Within a few seconds, 3–5 guesses appear. Pick one, edit one, or type your own in the last row, then **Save** (Ctrl+Enter). You can keep highlighting while guesses load; drafts wait in the sidebar.
4. Click **Finish & send**. The agent summarizes the technical and writing fixes it would make to the document and any style rules it would add or change, then applies them once you approve.

## How the live guessing works

The browser never calls a model directly. `scripts/feedback_server.py serve` queues each highlight in a session folder. The agent sits in a blocking `feedback_server.py next` call, which returns as soon as a highlight arrives. The agent then writes guesses using the text, its context from writing it, the style file, and your earlier comments, and goes back to waiting. No API key is needed, and the guesses come from the same agent that wrote the text (or, for your own writing, the agent that has read it). To keep guesses fast, the agent reads the document and notes its weak spots before the session starts, and each guess round is just two tool calls. For even faster guesses at some cost in quality, run `/effort low` before the session and switch back afterwards.

Session files go in `<document>.feedback/`. `comments.json` there keeps every comment, along with the guesses you were offered and whether you picked, edited, or replaced one.

## Remote machines (VS Code Remote-SSH, tmux)

The server runs on the machine where Claude Code runs, which may not be the machine in front of you. The agent can't reliably tell which screen you're at, so it never opens a browser on its own. Instead it prints a `localhost` URL for you to Ctrl+click. Over VS Code Remote-SSH, VS Code forwards the port and opens the page in your local browser, even when Claude Code runs inside tmux. If nothing opens, add the port in VS Code's Ports panel ("Forward a Port").

The server uses port 8765 (or the next free port), so a port VS Code already forwarded keeps working for later sessions.

## Math

LaTeX math (`$…$`, `$$…$$`, `\(…\)`, `\[…\]`, `\begin{align}` and similar) is typeset with KaTeX, which the page loads from a CDN. Offline, formulas show as their TeX source. A highlight that touches a formula covers the whole formula.
