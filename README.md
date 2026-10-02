# write-better

A Claude Code plugin with two skills that share one writing-style file. Each skill works on its own; together they form a loop where every round of feedback makes the next report better.

| Skill | What it does |
|---|---|
| `compose-report` | Makes the agent write a report like a careful human writer instead of in one shot. It outlines first, then drafts **one sentence at a time** on disk. After each sentence it re-reads the paragraph, after each paragraph the section, and after each section the whole report, revising each time against your style file. It ends with a fresh-reader subagent pass and a rule-by-rule style check. |
| `style-feedback` | Opens a local browser GUI on a markdown report. You highlight words or sentences, and the agent guesses your comment live in a drop-down. Each guess can be edited, and the last row is always "write my own". When you finish, the agent proposes report fixes and new or updated rules for your style file, and writes the rules only after you confirm. |

## Install

In Claude Code:

```
/plugin marketplace add C:\Users\slab\git\write-better
/plugin install write-better@write-better
```

Requirements: Python 3.8+ (standard library only) and any modern browser.

## The style file

Both skills use `~/.claude/writing-style.md` by default. To use a different file, set `WRITING_STYLE_FILE` or name a path in your request. The format is described in `skills/style-feedback/references/style-file-format.md`. Until the file exists, `compose-report` falls back to `skills/compose-report/references/default-style.md`.

## Typical use

1. Ask for research and a write-up, e.g. "Investigate X and write a report." `compose-report` triggers on report-writing tasks; you can also ask for it by name.
2. Say "let me give feedback on the report", or run `/style-feedback`. A browser tab opens.
3. Select text. A popover shows "Guessing your comment…". Within a few seconds, 3–5 guesses appear. Pick one, edit one, or type your own in the last row, then **Save** (Ctrl+Enter). You can keep highlighting while guesses load; drafts wait in the sidebar.
4. Click **Finish & send**. The agent summarizes the fixes it would make to the report and the style rules it would add or change, then applies them once you approve.

## How the live guessing works

The browser never calls a model directly. `scripts/feedback_server.py serve` queues each highlight in a session folder. The agent sits in a blocking `feedback_server.py next` call, which returns as soon as a highlight arrives. The agent then writes guesses using the report, its research context, the style file, and your earlier comments, and goes back to waiting. No API key is needed, and the guesses come from the same agent that wrote the report.

Session files go in `<report>.feedback/`. `comments.json` there keeps every comment, along with the guesses you were offered and whether you picked, edited, or replaced one.
