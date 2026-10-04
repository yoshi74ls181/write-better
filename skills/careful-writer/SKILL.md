---
name: careful-writer
description: Write or revise prose the way a careful human writer does, one sentence at a time, re-reading and revising at the sentence, paragraph, section, and document level against the user's writing-style file. Use whenever you are about to write prose someone will actually read: reports and research write-ups, papers or paper sections, abstracts, proposals, memos, documentation and READMEs, emails, letters, statements, blog posts, or a substantial rewrite of existing text. Also use when the user asks for careful, polished, or well-written prose. Do not write such text in one shot.
---

# careful-writer

You are writing for a **first-time reader**: someone intelligent who has not seen your research, your notes, or this conversation. Your job is to make every sentence make sense to that reader and follow the user's style. Writing in one pass doesn't do that. Write like a careful human writer: draft a little, re-read it from the page, revise, and only then go on.

Never write the text in one shot. Never compose the full text in your head and paste it in. The text grows on disk one sentence at a time, and each check reads the file again rather than relying on your memory of what you meant.

Below, **the piece** means whatever you are writing: a report, a paper section, an email, a README, and so on.

## Scale the process to the piece

The discipline is the same for every piece; only the amount of scaffolding changes.

- **Short** (a few paragraphs or less: an email, an abstract, a cover note, a single section). Keep the notes to a few lines on reader, purpose, and key points; they can live at the top of a scratch file instead of a separate notes file. Run the sentence loop and paragraph pass as written. The section pass becomes a re-read of the whole piece. The fresh-reader pass is optional unless the stakes are high (an application, a message to someone senior, anything that will be published).
- **Long** (a report, a paper, documentation with several sections). Follow every step below in full.

When unsure, treat the piece as long.

## Step 0: Load the style file

Find the style file in this order:
1. A path the user gave for this task.
2. The `WRITING_STYLE_FILE` environment variable (`echo $WRITING_STYLE_FILE`).
3. `~/.claude/writing-style.md`.

Read the whole file. If none exists, read `references/default-style.md` in this skill's directory and tell the user you're using the baseline style, which they can refine with the `doc-feedback` skill.

Also note any **conventions of the form** that apply: a venue's format, a template the user gave, the existing voice of a document you are adding to, or the norms of the genre (an email gets a clear ask; an abstract states the result; reference docs favor scannable structure). The user's style rules win when they conflict with genre habits.

Before drafting, list for yourself the 5–10 rules that matter most for this piece. Keep them in mind; you'll check every sentence against them.

## Step 1: Separate thinking from prose

Prose written straight from memory goes wrong, so write the material down first.

1. **Pick where the text lives.**
   - A new document: use the path the user asked for, or else a sensible name in the working directory (for example `report.md` or `proposal.md`).
   - An addition to an existing document (a new section of a paper, a paragraph in a README): write directly into that file at the right place. Read the surrounding text first so the new part fits it.
   - Text whose final home is not a file (an email, a message, a reply to paste somewhere): draft it in a scratch file and give the user the finished text at the end.
   - Use the file's own format (markdown, LaTeX, plain text, and so on). If the final format is one you can't edit sentence by sentence, such as `.docx`, draft in markdown and convert at the end.
2. Write `<stem>.notes.md` next to the draft (or a short header in the scratch file for short pieces). It holds:
   - **Reader**: who will read this, what they already know, and what they need to do afterward.
   - **Purpose**: one sentence on what the reader should understand, decide, or do after reading.
   - **Material**: the facts, numbers, sources, arguments, and caveats you will draw on, in rough form.
   - **Outline**: the sections in order (or just the paragraphs, for a short piece). For each, give its purpose in one line and its key points as bullets. Each bullet roughly becomes a paragraph.
3. Read the outline as the reader would. Does each part earn its place, and does the order build understanding? Fix the outline before writing prose.

## Step 2: Draft on disk, one sentence at a time

File layout: put **each paragraph on a single line** with a blank line between paragraphs, and headings on their own lines. Then `Read` with `offset`/`limit` can pull up one paragraph or one section cheaply, and `Edit` can target a sentence exactly. If you are adding to an existing file with a different layout, follow its layout instead.

Start with the title and the first section heading only (or just the opening line, for a piece without headings). Then, for every paragraph:

### Sentence loop (after every sentence)
1. Write the next sentence and append it to the current paragraph with `Edit` (or `Write` for the first line of a new file).
2. **Read the whole current paragraph from the file**, not from memory.
3. Check it against the **Sentence checks** in `references/checklists.md` and against the style rules you listed in Step 0. The key question: *Would a first-time reader, having read only what is above it, understand this sentence on the first read?*
4. If anything fails, rewrite the sentence with `Edit`, then go back to step 2. If it still fails after about 3 rewrites, keep the best version, add a `TODO(sentence)` line to the notes, and move on. The paragraph and section passes will revisit it.

### Paragraph pass (after every paragraph)
1. **Read the whole current section from the file** (the whole piece, if it has no sections).
2. Apply the **Paragraph checks** in `references/checklists.md`.
3. Edit the paragraph. You may also change sentences that came before it if the new paragraph shows they need it. After big changes, re-read the section once more.

### Section pass (after every section)
1. **Read the whole piece from the file.** If you are adding to a larger existing document, read your new part plus the text immediately around it.
2. Apply the **Section checks** in `references/checklists.md`.
3. Edit as needed, including earlier sections. Update the outline in the notes if the structure changed.
4. Write the next section heading and continue.

Don't batch these passes or skip them because a sentence "is obviously fine". Doing them every time is the point of this skill. Keep it cheap by reading only the paragraph or section you need.

## Step 3: Final passes

1. **Fresh-reader pass.** Spawn a subagent with the Agent tool and give it **only the draft path** and the intended reader: no notes, no research context. Use the fresh-reader prompt in `references/checklists.md`. Fix each spot it reports with the sentence loop (re-reading the paragraph after each fix).
2. **Style pass.** Go through the style file rule by rule. For each rule, scan the whole piece for violations and fix them.
3. **Read the whole piece once more**, start to finish.
4. Delete leftover `TODO(...)` notes that are resolved. Keep the notes file unless the user asks to remove it; delete scratch files for short pieces once the text is delivered.

## Step 4: Hand off

Tell the user where the piece is, in one or two sentences on what it covers, and mention any open `TODO`s or caveats. If the text's home is not a file, give the finished text itself. Then offer to collect their feedback with the `doc-feedback` skill. Their comments will improve this piece, and their writing preferences will update the style file the next piece uses.

## Revising existing text

When asked to revise, edit, or tighten text (yours or the user's, including after `doc-feedback`), apply the same discipline. Read the whole piece first and note its reader and purpose. Then, after each changed sentence, re-read its paragraph; after each changed paragraph, re-read its section; after finishing, re-read the whole piece. Keep the author's voice and leave alone what the user didn't ask you to change, unless a style rule clearly applies.
