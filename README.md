# write-better

A Claude Code plugin with two skills that share one writing-style file. Each skill works on its own; together they form a loop where every round of feedback makes the next piece better.

| Skill | What it does |
|---|---|
| `careful-writer` | Makes the agent write like a careful human writer instead of in one shot, for any prose that matters: reports, papers, proposals, docs, emails, statements, or a rewrite of existing text. It outlines first, then drafts **one sentence at a time** on disk. After each sentence it re-reads the paragraph, after each paragraph the section, and after each section the whole piece, revising each time against your style file. It ends with a fresh-reader subagent pass and a rule-by-rule style check. |
| `style-feedback` | Opens a local browser GUI on any piece of writing (converted to markdown if needed). You highlight words or sentences, and the agent guesses your comment live in a drop-down. Each guess can be edited, and the last row is always "write my own". When you finish, the agent proposes fixes to the text and new or updated rules for your style file, and writes the rules only after you confirm. |

## Install

In Claude Code:

```
/plugin marketplace add yoshi74ls181/write-better
/plugin install write-better@write-better
```

The first command registers this repo as a plugin marketplace; the second installs the plugin from it. To work from a local clone instead, pass its path to `/plugin marketplace add`.

Requirements: Python 3.8+ (standard library only) and any modern browser. Math typesetting needs internet access for KaTeX.

## The style file

Both skills use `~/.claude/writing-style.md` by default. To use a different file, set `WRITING_STYLE_FILE` or name a path in your request. The format is described in `skills/style-feedback/references/style-file-format.md`. Until the file exists, `careful-writer` falls back to `skills/careful-writer/references/default-style.md`.

## Typical use

1. Ask for a piece of writing, e.g. "Investigate X and write a report" or "Draft the related-work section." `careful-writer` triggers on writing tasks; you can also ask for it by name.
2. Say "let me give feedback on this", or name a file, or run `/style-feedback`. A browser tab opens.
3. Select text. A popover shows "Guessing your comment…". Within a few seconds, 3–5 guesses appear. Pick one, edit one, or type your own in the last row, then **Save** (Ctrl+Enter). You can keep highlighting while guesses load; drafts wait in the sidebar.
4. Click **Finish & send**. The agent summarizes the fixes it would make to the text and the style rules it would add or change, then applies them once you approve.

## How the live guessing works

The browser never calls a model directly. `scripts/feedback_server.py serve` queues each highlight in a session folder. The agent sits in a blocking `feedback_server.py next` call, which returns as soon as a highlight arrives. The agent then writes guesses using the text, its context from writing it, the style file, and your earlier comments, and goes back to waiting. No API key is needed, and the guesses come from the same agent that wrote the text (or, for your own writing, the agent that has read it). To keep guesses fast, the agent reads the document and notes its weak spots before the session starts, and each guess round is just two tool calls. For even faster guesses at some cost in quality, run `/effort low` before the session and switch back afterwards.

Session files go in `<document>.feedback/`. `comments.json` there keeps every comment, along with the guesses you were offered and whether you picked, edited, or replaced one.

## Remote machines (ssh, VS Code Remote-SSH, tmux)

The server always runs on the machine where Claude Code runs, and `feedback_server.py open` decides how to show you the window:

- **Local:** your default browser opens.
- **VS Code Remote-SSH:** the page opens in your local browser through VS Code, which forwards the port automatically. This works inside tmux too: inside tmux, `$BROWSER` and `code` point at whichever VS Code connection started the session, so `open` looks up the connected VS Code window when it runs. If no tab appears, open the printed URL with VS Code's "Simple Browser: Show", or from the Ports panel.
- **Plain ssh:** nothing can open from the remote side, so the agent gives you an `ssh -N -L <port>:127.0.0.1:<port> user@host` command to run on your own machine, then the URL to open.

Optionally, add `set -ga update-environment " VSCODE_IPC_HOOK_CLI"` to `~/.tmux.conf` on the remote machine. tmux then records the current VS Code connection each time you reattach from a VS Code terminal, which `open` prefers when several VS Code windows are connected.

## Math

LaTeX math (`$…$`, `$$…$$`, `\(…\)`, `\[…\]`, `\begin{align}` and similar) is typeset with KaTeX, which the page loads from a CDN. Offline, formulas show as their TeX source. A highlight that touches a formula covers the whole formula.
