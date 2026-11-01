---
name: careful-writer
description: Write or revise prose the way a careful human writer does, one sentence at a time, re-reading and revising at the sentence, paragraph, section, and document level against the user's writing rules, fetched fresh each time. Use whenever you are about to write prose someone will actually read: reports and research write-ups, papers or paper sections, abstracts, proposals, memos, documentation and READMEs, emails, letters, statements, blog posts, or a substantial rewrite of existing text. Also use for a single sentence or paragraph added in passing, such as a README line or a message a program shows people, written during a code change. Also use when the user asks for careful, polished, or well-written prose. Do not write such text in one shot.
---

# careful-writer

This skill is a workflow: how to draft, re-read and revise so that the user's writing rules hold in every sentence. The rules themselves, including the checks to run at each step and the reader to write for, come from the user and are loaded in Step 0. Apply what they say; this file says only when and how to apply it.

Never write the text in one shot. Never compose the full text in your head and paste it in. The text grows on disk one sentence at a time, and each check reads the file again rather than relying on your memory of what you meant.

Below, **the piece** means whatever you are writing: a report, a paper section, an email, a README, and so on. **The rules** means everything Step 0 loads, and **the checks** means the sentence, paragraph and section checks and the fresh-reader prompt among them.

## Scale the process to the piece

The discipline is the same for every piece; only the amount of scaffolding changes.

- **Tiny** (a sentence or a paragraph added while doing other work: a README line, a docstring a user reads, a message a program shows people). Skip the notes and the outline. Still run the sentence loop on every sentence. At the end, re-read the paragraph and the text around it once. Text written in passing is where crowded sentences slip in, so don't skip this tier.
- **Short** (a few paragraphs or less: an email, an abstract, a cover note, a single section). Keep the notes to a few lines on reader, purpose, and key points; they can live at the top of a scratch file instead of a separate notes file. Run the sentence loop and paragraph pass as written. The section pass becomes a re-read of the whole piece. The fresh-reader pass is optional unless the stakes are high (an application, a message to someone senior, anything that will be published, such as a README or a message a program sends).
- **Long** (a report, a paper, documentation with several sections). Follow every step below in full.

When unsure, treat the piece as long.

## Step 0: Load the rules

Find the user's rules in this order, and use the first source that exists:
1. A path the user gave for this task.
2. A rules repository, fetched fresh from GitHub. Run `python "<skill-dir>/scripts/rules.py" fetch`, where `<skill-dir>` is this skill's base directory. It reads the repository named by the `WRITING_RULES_REPO` environment variable, downloads the rule files from the latest commit on its `main` branch, and prints them as JSON. `"source": "none"` means no repository is configured; go on to item 3. Otherwise read the local copy of `index.md`, then read in full every file whose "read when" condition holds for this piece. Tell the user the short commit (the first 7 characters of `commit`) the rules came from. If `source` is `cache`, also say that GitHub couldn't be reached and give the date of the cached copy. Fetch again for each new piece, so that rules added in the meantime apply.
3. The `WRITING_STYLE_FILE` environment variable (`echo $WRITING_STYLE_FILE`).
4. `~/.claude/writing-style.md`.

Read every file that applies, in full. If none exists, tell the user they have no writing rules yet, so the passes below have nothing to check against, and offer the `doc-feedback` skill to start them from their feedback. Then write with the workflow alone.

Also note any **conventions of the form** that apply: a venue's format, a template the user gave, the existing voice of a document you are adding to, or the norms of the genre (an email gets a clear ask; an abstract states the result; reference docs favor scannable structure). The rules win when they conflict with these conventions.

Before drafting, list for yourself the 5–10 rules that matter most for this piece. Keep them in mind; you'll check every sentence against them.

## Step 1: Separate thinking from prose

Prose written straight from memory goes wrong, so write the material down first.

1. **Pick where the text lives.**
   - A new document: use the path the user asked for, or else a sensible name in the working directory (for example `report.md` or `proposal.md`).
   - An addition to an existing document (a new section of a paper, a paragraph in a README): write directly into that file at the right place. Read the surrounding text first so the new part fits it.
   - Text whose final home is not a file (an email, a message, a reply to paste somewhere): draft it in a scratch file and give the user the finished text at the end.
   - Use the file's own format (markdown, LaTeX, plain text, and so on). If the final format is one you can't edit sentence by sentence, such as `.docx`, draft in markdown and convert at the end.
2. Write `<stem>.notes.md` next to the draft (or a short header in the scratch file for short pieces). It holds:
   - **Reader**: who will read this, what they already know, and what they need to do afterward. Start from the reader the rules describe, if they describe one.
   - **Purpose**: one sentence on what the reader should understand, decide, or do after reading.
   - **Material**: the facts, numbers, sources, arguments, and caveats you will draw on, in rough form. Mark each one *must* (the reader needs it to understand or to act) or *nice*.
   - **Outline**: the sections in order (or just the paragraphs, for a short piece). For each, give its purpose in one line and its key points as bullets. Each bullet roughly becomes a paragraph. Give each paragraph its *must* facts, and decide where each *nice* fact could go.
3. Read the outline as the reader would. Does each part earn its place, and does the order build understanding? Fix the outline before writing prose.

## Step 2: Draft on disk, one sentence at a time

File layout: lay out the source as the rules say, for example one sentence per line. If they say nothing, put each paragraph on a single line with a blank line between paragraphs, and headings on their own lines. Either way `Read` with `offset`/`limit` can pull up one paragraph or one section cheaply, and `Edit` can target a sentence exactly. If you are adding to an existing file with a different layout, follow its layout instead.

Start with the title and the first section heading only (or just the opening line, for a piece without headings). Then, for every paragraph:

### Sentence loop (after every sentence)
1. Write the next sentence and append it to the current paragraph with `Edit` (or `Write` for the first line of a new file).
2. **Read the whole current paragraph from the file**, not from memory.
3. Check it against the sentence checks and against the rules you listed in Step 0.
4. If anything fails, rewrite the sentence with `Edit`, then go back to step 2. If it still fails after about 3 rewrites, keep the best version, add a `TODO(sentence)` line to the notes, and move on. The paragraph and section passes will revisit it.

### Paragraph pass (after every paragraph)
1. **Read the whole current section from the file** (the whole piece, if it has no sections).
2. Apply the paragraph checks.
3. Edit the paragraph. You may also change sentences that came before it if the new paragraph shows they need it. After big changes, re-read the section once more.

### Section pass (after every section)
1. **Read the whole piece from the file.** If you are adding to a larger existing document, read your new part plus the text immediately around it.
2. Apply the section checks.
3. Edit as needed, including earlier sections. Update the outline in the notes if the structure changed.
4. Write the next section heading and continue.

Don't batch these passes or skip them because a sentence "is obviously fine". Doing them every time is the point of this skill. Keep it cheap by reading only the paragraph or section you need.

## Step 3: Final passes

1. **Fresh-reader pass.** Spawn a subagent with the Agent tool and give it **only the draft path** and the intended reader: no notes, no research context. Use the fresh-reader prompt from the checks. Fix each spot it reports with the sentence loop (re-reading the paragraph after each fix).
2. **Rules pass.** Go through the rules one by one. For each rule, scan the whole piece for violations and fix them.
3. **Read the whole piece once more**, start to finish.
4. Delete leftover `TODO(...)` notes that are resolved. Keep the notes file unless the user asks to remove it; delete scratch files for short pieces once the text is delivered.

## Step 4: Hand off

Tell the user where the piece is, in one or two sentences on what it covers, and mention any open `TODO`s or caveats. If the text's home is not a file, give the finished text itself. Then offer to collect their feedback with the `doc-feedback` skill. Their comments will improve this piece, and their writing preferences will update the rules the next piece uses.

## Revising existing text

When asked to revise, edit, or tighten text (yours or the user's, including after `doc-feedback`), apply the same discipline. Load the rules as in Step 0, then read the whole piece and note its reader and purpose. After each changed sentence, re-read its paragraph and run the sentence checks; after each changed paragraph, re-read its section; after finishing, re-read the whole piece. Keep the author's voice and leave alone what the user didn't ask you to change, unless a rule clearly applies.
