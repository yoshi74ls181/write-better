# Style file format

The user's rules live in one of two places, and `careful-writer` reads them while `doc-feedback` maintains them:

- A **rules repository** on GitHub, named by the `WRITING_RULES_REPO` env var (`owner/name`). Its `index.md` holds a table whose rows each name a rule file in backticks and say when to read it, and the skills fetch the files from the latest commit on `main` every time they run. Changes go straight to `main` (`doc-feedback` Step 4). If the repository's README sets its own conventions for writing rules, follow them.
- A single **style file**: default `~/.claude/writing-style.md`, overridden by the `WRITING_STYLE_FILE` env var or an explicit path.

Either way the rules are plain markdown. Keep each file short enough to read in full before every piece of writing, roughly under 300 lines. Merge rules rather than piling them up.

```markdown
# Writing style

## Reader and voice

The default reader is <who they are, what they already know>.
Write <e.g. plainly and directly; first-person plural is fine; no marketing tone>.
Use <e.g. US English, with the Oxford comma>.

## Rules

### R1. <Short imperative title>

<What to do, stated so it can be checked on a single sentence or paragraph.>

- Bad → Good: "<real example the user flagged>" → "<fixed version>"

### R2. ...
```

Conventions:
- State the rule. Add how it fails only where that tells the writer how to check, and in one clause. Leave out the reasons for the rule and the incident that earned it; in a rules repository they go in the commit message.
- Number rules `R1`, `R2`, … and never reuse a number. If a rule is deleted, leave a gap. In a rules repository the numbers are shared by all its files, and a rule moved between files keeps its number.
- One rule, one checkable behavior. Split rules that cover two things.
- When feedback **reinforces** a rule, add another example only if it shows a new case.
- When feedback **conflicts** with a rule, don't keep both. Rewrite the rule to state the narrower or newer preference.
- These files hold only **writing** preferences that carry over to future documents. Facts and decisions specific to one document ("call the dataset X") and technical feedback on one document ("this proof misses the boundary case", "use a log scale in Figure 2") belong in that document, not here.
- Write rules in plain language and avoid style-guide jargon unless the user uses it.
