---
name: doc-feedback
description: Collect the user's feedback on a document (a report, paper, proposal, doc, email draft, or any other text) through a local browser GUI. The user highlights words or sentences, or picks a whole paragraph, section, or the entire document, and the agent guesses the likely comment live (offered as editable options, of which the user can tick one or several); afterwards the comments become fixes to the document. Feedback can be technical (correctness, derivations, methods, missing results, code) or about the writing. Only writing preferences that carry over to future documents go into the user's shared writing-style file (~/.claude/writing-style.md), which the careful-writer skill reads. Use when the user wants to review, mark up, comment on, or give feedback on a document, or wants to teach or update their writing style.
---

# doc-feedback

You run a highlight-and-comment session on a document, rendered from markdown. The user does the reading and judging, and their comments can be about the content (is this right, is something missing, is this the right method) or about the writing. Your job during the session is to **guess their comment quickly and well**, so most of the time they just pick a guess or tweak one. At the end you turn what they said into fixes to this document, and, for writing preferences that carry over, rules in the shared style file, so the next document needs less feedback.

`<skill-dir>` below means this skill's base directory, shown when the skill loads. Use `python` on Windows and `python3` elsewhere if `python` is missing.

## Step 1: Set up

1. **Document**: the path the user names, or else the document you just wrote. If it isn't markdown (LaTeX, plain text, `.docx`, and so on), convert it to a `.md` copy first and say so; apply the fixes to the original afterward. If the text isn't in a file at all (an email draft, a pasted passage), save it to a `.md` file first.
2. **Style file**: an explicit path from the user, then `$WRITING_STYLE_FILE`, then `~/.claude/writing-style.md`. Read it now if it exists, along with `references/style-file-format.md`.
3. **Read the document in full** now, even if you wrote it, and note for yourself its likely weak spots of both kinds:
   - **Technical**: claims that may be wrong or unsupported, gaps in a derivation or argument, inconsistent numbers, units, or notation, questionable methods or assumptions, missing results, comparisons, or citations, and code that may not do what the text says.
   - **Writing**: style-rule violations, undefined terms, hedges, unclear or clumsy sentences, poor ordering.
   - **Figures**: open each image the document embeds with the Read tool (an animated GIF may show as a single frame). Note labels or tick numbers too small to read, axes without labels or units, a legend or colours that don't match the text, a caption that doesn't say what to look at, and a figure that doesn't show what the text claims.

   Do your thinking here, so that during the loop each guess is mostly recall.
4. **Session dir**: `<doc-dir>/<doc-stem>.feedback/`. Reusing an existing dir starts a new round and keeps the earlier comments that haven't been resolved (Step 4). If `comments.json` already holds comments, check each against the document as it is now, and resolve the ones whose fix is already in it before you start the server. Sessions from older versions of this skill never resolved anything, so they may hold many.
5. Start the server **in the background** (Bash with `run_in_background: true`):
   ```
   python "<skill-dir>/scripts/feedback_server.py" serve --document "<document>" --session "<session-dir>"
   ```
6. Get the address. Run, in the **foreground**:
   ```
   python "<skill-dir>/scripts/feedback_server.py" url --session "<session-dir>"
   ```
   It waits for the server, then prints `url`, `port`, `tailscale`, and a ready-made message for the user, which includes the steps for forwarding the port over VS Code Remote-SSH. If Tailscale is installed and signed in on this machine, it also shares the GUI on the user's tailnet so they can open it on a phone, and the message gives that address. Add `--no-tailscale` if the user doesn't want that.
7. Give the user the URL and wait for their first highlight:
   1. Start the first wait **in the background** (Bash with `run_in_background: true`):
      ```
      python "<skill-dir>/scripts/feedback_server.py" next --session "<session-dir>" --timeout 86400
      ```
   2. **End your turn, with the message from `url` as your whole reply.** Send it as plain text, not in a code block or quote, and keep the URL alone on its line with a blank line above and below it, so it's easy to spot and Ctrl+clickable in the terminal. Don't write the message only in your reasoning: the user sees at most a summary of your reasoning, where the URL can't be clicked. The reply that ends a turn is always shown, which is why you end the turn here.
   3. When the background `next` finishes, you are invoked again. Read its output and handle it as in Step 2 (for a highlight, write the guesses), then run the loop in the foreground from there. If the user writes to you before that, answer them and leave the background `next` running.

   **Don't open a browser yourself** (no `$BROWSER`, `xdg-open`, `start`, or `code`): the user may be working through VS Code Remote-SSH, often inside tmux, and a browser opened from here would land on the wrong screen. If the user says they're at this machine and asks you to open it, you may.

## Step 2: Guess loop

The user is waiting from the moment they highlight until the guesses appear, so the loop is built for speed. Each round is **exactly two tool calls**, `next` and then `Write`, with no text output, no file reads, and no other tools between them. Only the first wait, in Step 1, runs in the background.

Repeat until the session is done:

1. Run, in the **foreground** with Bash `timeout: 600000`:
   ```
   python "<skill-dir>/scripts/feedback_server.py" next --session "<session-dir>"
   ```
   It blocks until something happens and prints one JSON object:
   - `{"idle": true}`: nothing yet. Run `next` again immediately.
   - `{"done": true, ...}`: the user finished. Go to Step 3.
   - A highlight: `id`, `scope`, `text`, `figure`, `paragraph`, `section`, `guesses_path`, `queue_remaining`, and `prior_comments` (everything saved so far this session, with `source` showing whether they picked guesses as is (`guess`), edited one (`edited-guess`), wrote their own (`own`), or combined these (`mixed`)). Math arrives as its TeX source, such as `$a_i$`. `scope` says what the comment is about: `selection` (the highlighted passage in `text`), `paragraph` (the whole paragraph, also in `text`), `section` (the whole section; `text` is only its heading), `document` (the whole document; `text` is only its file name), or `figure` (one figure; `text` is its caption, taken from the image's alt text, and `figure` is the image's path relative to the document).
2. Write **3–5 guesses** with the Write tool to `guesses_path`, as exactly `{"guesses": ["...", "..."]}`. Decide quickly: use what you noted in Step 1 and the guidance below, and don't deliberate over wording or order.
3. Go back to step 1 at once. Don't stop to comment, summarize, or check on the user between rounds.

### What makes a good guess
- Write it **in the user's voice, as the comment they'd type**, and make it specific to this text: "Define 'ELBO' here, first use" or "This bound needs $L$-smoothness; state it", not "Clarity issue" or "Check this". Keep it under about 20 words, and add a concrete fix where natural ("→ 'latency fell from 120 ms to 45 ms'").
- **Cover both kinds.** Unless the session so far is clearly about only one kind, include at least one technical guess and at least one writing guess.
- **Rank by likelihood.** Consider these sources, in order:
  1. **Prior comments this session.** Users repeat themselves. If they flagged hedging twice, a hedge in the new selection is the top guess. If their comments have been mostly technical, lead with technical guesses. If they kept editing your guesses the same way (for example, making them shorter or blunter), write that way.
  2. **Your Step 1 notes** on this passage, technical or writing.
  3. **Style-file rules** that the selected text breaks.
  4. **What the selection suggests.** An equation, number, or symbol suggests a correctness, notation, or units question. A claim suggests "is this right / what's the evidence / cite it". A single word suggests word choice, an undefined term, or jargon. A phrase suggests wordiness, vagueness, or a hedge. A whole sentence suggests that it's wrong, unsupported, unclear, too long, in the wrong place, or unneeded.
- **For a whole paragraph, section, or document** (`scope` `paragraph`, `section`, or `document`), guess about the unit as a whole, not about one sentence in it. For a paragraph: its point, its topic sentence, the order of its sentences, its length, or whether it belongs here. For a section: whether it answers the question it opens with, its structure, what's missing, or whether it should move, merge, or go. For the document: its main claim, its framing, its overall structure, its length, and its gaps. For a section or the document, the record carries only a heading or a file name, so draw on your Step 1 notes.
- **For a figure** (`scope` `figure`), guess from what you noted when you looked at it in Step 1: legibility, axes and units, legend and colours, the caption, whether it shows what the text says, and, for an animation, its speed and length.
- Make the guesses **different from each other**, each a distinct reading of why the user highlighted this. The user can tick several guesses for one highlight, so write each as a self-contained point that still reads well next to the others.
- **Never offer a "fine as it is" guess** ("Good. Keep this", "No change needed", and the like). The user highlighted the text because something about it caught their attention, so every guess should name a specific change or question. When the text has no obvious problem, look harder: correctness, missing justification, word choice, emphasis, placement, or whether it's needed at all.

## Step 3: Digest

Read `<session-dir>/comments.json`. Each item has `scope`, `text`, `paragraph`, `section`, `comment`, `source`, `parts`, and the `guesses` you offered. `comment` joins the rows the user ticked, one per line, and `parts` lists them separately, each with its own `text`, `source`, and `guess_index`. Comments saved before multi-select have no `parts`; treat their `comment` as a single part. Sort each part on its own below, since the parts of one comment can be of different kinds.

Sort every comment into one of three kinds:
- **(a) Technical, this document**: about the content of this document (a wrong claim or equation, a gap in an argument, a missing experiment or citation, a method choice, a bug in included code, "this contradicts Table 2").
- **(b) Writing, this document**: a writing fix that only makes sense here ("move this to the intro", "this sentence is confusing").
- **(c) Writing preference**: how the user wants things written in general, which should apply to future documents too ("don't use 'leverage'", "define acronyms", "too hedgy", "give units with every number").

One comment can be both (b) and (c): fix it here and record the preference.

**Only (c) goes into the shared style file.** Technical feedback about this document stays with this document, even when it's phrased generally ("always check the boundary case" about this proof is (a), not a rule). A general preference about how to *present* technical material, such as "state assumptions before the theorem", can be (c). When you can't tell whether a writing comment generalizes, treat it as (b) and ask in the summary.

For (c), group comments that express the same preference and draft one rule per group in the style-file format: **Rule**, **Why**, **Bad → Good** (from the user's actual highlight), and **Source**. For each rule, decide whether it's **new**, **reinforces** an existing rule (add a source and maybe an example), or **conflicts** with one (rewrite the old rule; don't keep both).

Show the user one compact summary:
- **Technical fixes** to this document. For each, say what you'll change. Flag the ones that need work beyond editing, such as re-deriving a result, checking a source, rerunning code, or adding an experiment, and the ones where you're unsure what the right fix is.
- **Writing fixes** to this document.
- **Style-file changes**: new, reinforced, or changed rules.
- Your guess hit rate (counting parts: how many were picked guesses, edited guesses, or own words). It's useful feedback for you, and the user may find it interesting.

## Step 4: Apply

1. **Edits to the document.** Ask whether to apply the fixes (default: yes, all of (a) and (b), plus the (c) violations found in this document). For technical fixes, do the work before you write: re-derive, check the source, or run the code, and don't paper over a problem you couldn't resolve. Mark it in the text or tell the user instead. Revise carefully: if the `careful-writer` skill is available, follow its "Revising existing text" discipline. In any case, re-read the paragraph after each changed sentence and the whole document at the end. Don't touch text the user didn't comment on unless a style rule clearly applies or a technical fix requires it (for example, a corrected number that appears in two places).
2. **Style file.** Only if there are (c) changes. Show the proposed change as a diff, or as the full new file if it's being created. If the file doesn't exist yet, start from `<skill-dir>/../careful-writer/references/default-style.md` if the user wants the baseline rules, or else from just the header sections. Write it **only after the user confirms**. Keep the file tight: merge, don't append duplicates.
3. **Resolve what's done.** Run this with the `id` of every comment whose fix you made in full, and of every comment the user chose to drop:
   ```
   python "<skill-dir>/scripts/feedback_server.py" resolve --session "<session-dir>" <id> [<id> ...]
   ```
   It moves those comments from `comments.json` to `resolved.json`, so the next round doesn't show them again. Leave in `comments.json` only the comments that still need work, such as a fix you couldn't finish, and tell the user which ones they are.
4. Offer another round, where the user reviews the revised document the same way. If they accept, restart the server against the same session dir (comments you didn't resolve stay in the sidebar; the port usually stays the same, so the user can just reload the page), re-read the revised document as in Step 1, give the user the URL and wait for the first highlight as in Step 1 (steps 6 and 7), and repeat Step 2.

## Step 5: Clean up

```
python "<skill-dir>/scripts/feedback_server.py" stop --session "<session-dir>"
```
Keep `comments.json` and `resolved.json` (they're the user's record) unless the user asks to remove the session dir.

## Notes
- Besides selecting text, the user can comment on a whole paragraph (¶ in the left margin), a whole section (§ next to its heading), the whole document (a button in the header), or a figure (Fig in the margin). Clicking an animated figure pauses it, with ⏸️ over it, and clicking again resumes it. Each of these holds one comment, and older `comments.json` files without `scope` are read as selections.
- On a touch screen, such as a phone, selecting text brings up a **Comment on selection** button at the bottom of the screen, since a selection made with handles has no mouse release to end it.
- The GUI lets the user type their own comment before the guesses arrive. If a highlight gets a comment first, or the user cancels it, `next` stops returning it, so no guess turn is wasted on it. If they cancel it while you're writing its guesses, write them anyway; the next `next` deletes them.
- Starting `serve` for a session stops the server already running for it, so the new one takes its port and a reloaded tab shows the new page.
- The server uses port 8765, or the next free port if that's taken, so a port VS Code already forwarded keeps working across sessions. If the port changed, give the new URL and use the new port in the forwarding steps.
- Over VS Code Remote-SSH, VS Code usually forwards the port by itself once the server starts, lists it in the Ports tab, and opens the link in the user's local browser. When it doesn't, the user forwards the port by hand with the steps in the URL message. If port 8765 is already busy on the user's own computer, VS Code forwards it to a different local port; the page is then at the address in the Forwarded Address column, not at the URL you gave.
- **From a phone or tablet.** `url` runs `tailscale serve --bg --https=<port> http://127.0.0.1:<port>`, which serves the GUI at `https://<machine>.<tailnet>.ts.net:<port>/` to the user's own devices only; the server itself stays on `127.0.0.1`. The server takes that address down when it stops. The `tailscale` line of `url`'s output says what happened:
  - An `https://…ts.net` address: it's in the message.
  - A `login.tailscale.com` link: HTTPS isn't enabled for the tailnet yet. The message asks the user to approve it; once they have, run `url` again and give them the new message.
  - `none (…)`: Tailscale isn't installed, running, or signed in. If the user asks how to set it up: install Tailscale on this machine and on the phone, sign in to the same account on both, turn it on, then ask you to run `url` again.

  Don't suggest binding the server to `0.0.0.0` instead: the server has no login, so anyone on the network could read the document.
- The header shows "agent listening" while `next` is waiting. If the loop stalls (for example, you were interrupted), just run `next` again. Queued highlights are kept.
- Images the document embeds by a relative path (PNG, JPEG, GIF, SVG, and WebP) are served from the document's folder and its subfolders. Images elsewhere don't show in the GUI.
- LaTeX math (`$…$`, `$$…$$`, `\(…\)`, `\[…\]`, `\begin{align}` and similar) is typeset in the GUI with KaTeX, loaded from a CDN. Offline, formulas show as TeX source. Either way, a highlight that touches a formula covers the whole formula, and its text arrives as TeX source.
- Using this skill alone, without careful-writer, works: any markdown file can be reviewed, and the style file is still updated with writing preferences.
