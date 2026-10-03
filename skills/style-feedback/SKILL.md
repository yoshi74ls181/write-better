---
name: style-feedback
description: Collect the user's feedback on a piece of writing (a report, paper, proposal, doc, email draft, or any other text) through a local browser GUI. The user highlights words or sentences, the agent guesses the likely comment live (offered in an editable drop-down), and afterwards the comments become edits to the text and lasting rules in the user's writing-style file (~/.claude/writing-style.md), which the careful-writer skill reads. Use when the user wants to review, mark up, or give feedback on something written, or wants to teach or update their writing style.
---

# style-feedback

You run a highlight-and-comment session on a piece of writing, rendered from markdown. The user does the reading and judging; your job is to **guess their comment quickly and well**, so most of the time they just pick a guess or tweak one. At the end you turn what they said into (a) fixes to this piece and (b) rules in the style file, so the next piece needs less feedback.

`<skill-dir>` below means this skill's base directory, shown when the skill loads. Use `python` on Windows and `python3` elsewhere if `python` is missing.

## Step 1: Set up

1. **Document**: the path the user names, or else the piece you just wrote. If it isn't markdown (LaTeX, plain text, `.docx`, and so on), convert it to a `.md` copy first and say so; apply the fixes to the original afterward. If the text isn't in a file at all (an email draft, a pasted passage), save it to a `.md` file first.
2. **Style file**: an explicit path from the user, then `$WRITING_STYLE_FILE`, then `~/.claude/writing-style.md`. Read it now if it exists. You'll use its rules as guess material, and you won't re-read it during the loop. Read `references/style-file-format.md` too.
3. **Session dir**: `<doc-dir>/<doc-stem>.feedback/`. Reusing an existing dir keeps the earlier comments and starts a new round.
4. Start the server **in the background** (Bash with `run_in_background: true`):
   ```
   python "<skill-dir>/scripts/feedback_server.py" serve --document "<document>" --session "<session-dir>"
   ```
   It opens the browser itself. Read `<session-dir>/server.json` for the URL and give it to the user in one line: "Select text to comment; I'll suggest comments; click **Finish & send** when done."

## Step 2: Guess loop

Repeat until the session is done:

1. Run, in the **foreground** with Bash `timeout: 600000`:
   ```
   python "<skill-dir>/scripts/feedback_server.py" next --session "<session-dir>"
   ```
   It blocks until something happens and prints one JSON object:
   - `{"idle": true}`: nothing yet. Run `next` again right away, without commentary.
   - `{"done": true, ...}`: the user finished. Go to Step 3.
   - A highlight: `id`, `text` (the selection), `paragraph`, `section`, `guesses_path`, `queue_remaining`, and `prior_comments` (everything saved so far this session, with `source` showing whether they picked a guess as is, edited one, or wrote their own).
2. Write **3–5 guesses** and save them with the Write tool to `guesses_path`, as exactly `{"guesses": ["...", "..."]}`. The user is waiting while you do this, so think briefly, then write. Don't read other files or narrate in between.
3. Go back to step 1 at once.

### What makes a good guess
- Write it **in the user's voice, as the comment they'd type**, and make it specific to this text: "Define 'ELBO' here, first use", not "Clarity issue". Keep it under about 20 words, and add a concrete fix where natural ("→ 'latency fell from 120 ms to 45 ms'").
- **Rank by likelihood.** Consider these sources, in order:
  1. **Prior comments this session.** Users repeat themselves. If they flagged hedging twice, a hedge in the new selection is the top guess. If they kept editing your guesses the same way (for example, making them shorter or blunter), write that way.
  2. **Style-file rules** that the selected text breaks.
  3. **What the selection's size suggests.** A single word suggests word choice, an undefined term, or jargon. A phrase suggests wordiness, vagueness, or a hedge. A whole sentence suggests that it's unclear, too long, unsupported, in the wrong place, or unneeded.
  4. **Content doubts.** Is this claim correct or sourced? Is it the right emphasis? Is something missing?
- Make the guesses **different from each other**, each a distinct reading of why the user highlighted this. Include one guess that isn't a complaint ("Good. Keep this framing") when the text has no obvious problem.

## Step 3: Digest

Read `<session-dir>/comments.json`. Each item has `text`, `paragraph`, `section`, `comment`, `source`, and the `guesses` you offered.

Sort every comment into one of two kinds:
- **(a) This piece only**: a fix that only makes sense for this text (a wrong fact, a missing result, "move this to the intro").
- **(b) Style preference**: something that should apply to future writing too ("don't use 'leverage'", "define acronyms", "too hedgy"). One comment can be both.

For (b), group comments that express the same preference and draft one rule per group in the style-file format: **Rule**, **Why**, **Bad → Good** (from the user's actual highlight), and **Source**. For each rule, decide whether it's **new**, **reinforces** an existing rule (add a source and maybe an example), or **conflicts** with one (rewrite the old rule; don't keep both).

Show the user one compact summary: the fixes to the piece as a list, and the style changes as new, reinforced, or changed rules. Note your guess hit rate (how many comments were a picked guess, an edited guess, or own words). It's useful feedback for you, and the user may find it interesting.

## Step 4: Apply

1. **Edits to the piece.** Ask whether to apply the fixes (default: yes, both (a) and the (b) violations found in this piece). Revise carefully: if the `careful-writer` skill is available, follow its "Revising existing text" discipline. In any case, re-read the paragraph after each changed sentence and the whole piece at the end. Don't touch text the user didn't comment on unless a style rule clearly applies.
2. **Style file.** Show the proposed change as a diff, or as the full new file if it's being created. If the file doesn't exist yet, start from `<skill-dir>/../careful-writer/references/default-style.md` if the user wants the baseline rules, or else from just the header sections. Write it **only after the user confirms**. Keep the file tight: merge, don't append duplicates.
3. Offer another round, where the user reviews the revised piece the same way. If they accept, restart the server against the same session dir (the old comments stay visible in the sidebar) and repeat Step 2.

## Step 5: Clean up

```
python "<skill-dir>/scripts/feedback_server.py" stop --session "<session-dir>"
```
Keep `comments.json` (it's the user's record) unless the user asks to remove the session dir.

## Notes
- The GUI lets the user type their own comment before your guesses arrive. If a highlight gets a comment first, `next` stops returning it, so you never waste a turn on it.
- The header shows "agent listening" while `next` is waiting. If the loop stalls (for example, you were interrupted), just run `next` again. Queued highlights are kept.
- Using this skill alone, without careful-writer, works: any markdown file can be reviewed, and the style file is still updated.
