# Style file format

The style file (default `~/.claude/writing-style.md`, overridden by the `WRITING_STYLE_FILE` env var or an explicit path) is plain markdown. `compose-report` reads it and `style-feedback` maintains it. Keep it short enough to read in full before every report, roughly under 300 lines. Merge rules rather than piling them up.

```markdown
# Writing style

## Reader & voice
- Default reader: <who they are, what they already know>
- Voice: <e.g. plain, direct, first-person plural is fine, no marketing tone>
- Language/locale: <e.g. US English, Oxford comma>

## Rules

### R1. <Short imperative title>
- **Rule:** <What to do, stated so it can be checked on a single sentence or paragraph.>
- **Why:** <The reason, in the user's terms. This lets the writer handle edge cases.>
- **Bad → Good:** "<real example the user flagged>" → "<fixed version>"
- **Source:** <report file name>, <YYYY-MM-DD> (add more sources as the rule is reinforced)

### R2. ...
```

Conventions:
- Number rules `R1`, `R2`, … and never reuse a number. If a rule is deleted, leave a gap.
- One rule, one checkable behavior. Split rules that cover two things.
- When feedback **reinforces** a rule, add a source line, and add another example only if it shows a new case.
- When feedback **conflicts** with a rule, don't keep both. Rewrite the rule to state the narrower or newer preference, and note the change in **Why**.
- Put report-specific facts (e.g. "call the dataset X") in the report, not here. This file holds only preferences that carry over to future writing.
- Write rules in plain language and avoid style-guide jargon unless the user uses it.
