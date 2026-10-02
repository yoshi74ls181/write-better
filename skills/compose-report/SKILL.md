---
name: compose-report
description: Write a report, write-up, memo, or summary of research findings the way a careful human writer does, one sentence at a time, re-reading and revising at the sentence, paragraph, section, and report level against the user's writing-style file. Use whenever you are about to write up the results of a research or investigation task, or the user asks for a report or careful prose. Do not write such reports in one shot.
---

# compose-report

You are writing for a **first-time reader**: someone intelligent who has not seen your research, your notes, or this conversation. Your job is to make every sentence make sense to that reader and follow the user's style. Writing in one pass doesn't do that. Write like a careful human writer: draft a little, re-read it from the page, revise, and only then go on.

Never write the report in one shot. Never write the full text in your head and paste it in. The report grows on disk one sentence at a time, and each check reads the file again rather than relying on your memory of what you meant.

## Step 0: Load the style file

Find the style file in this order:
1. A path the user gave for this task.
2. The `WRITING_STYLE_FILE` environment variable (`echo $WRITING_STYLE_FILE`).
3. `~/.claude/writing-style.md`.

Read the whole file. If none exists, read `references/default-style.md` in this skill's directory and tell the user you're using the baseline style, which they can refine with the `style-feedback` skill.

Before drafting, list for yourself the 5–10 rules that matter most for this report. Keep them in mind; you'll check every sentence against them.

## Step 1: Separate thinking from prose

Prose written straight from memory goes wrong, so write the material down first.

1. Pick the report path. Use the one the user asked for, or else a sensible name such as `report.md` in the working directory.
2. Write `<report-stem>.notes.md` next to it. It holds:
   - **Reader**: who will read this, what they already know, and what they need to do afterward.
   - **Purpose**: one sentence on what the reader should understand or decide after reading.
   - **Findings**: the facts, numbers, sources, and caveats from your research, in rough form.
   - **Outline**: the sections in order. For each section, give its purpose in one line and its key points as bullets. Each bullet roughly becomes a paragraph.
3. Read the outline as the reader would. Does each section earn its place, and does the order build understanding? Fix the outline before writing prose.

## Step 2: Draft on disk, one sentence at a time

File layout: put **each paragraph on a single line** with a blank line between paragraphs, and headings on their own lines. Then `Read` with `offset`/`limit` can pull up one paragraph or one section cheaply, and `Edit` can target a sentence exactly.

Start the file with the title and the first section heading only. Then, for every paragraph:

### Sentence loop (after every sentence)
1. Write the next sentence and append it to the current paragraph's line with `Edit` (or `Write` for the first line of the file).
2. **Read the whole current paragraph from the file**, not from memory.
3. Check it against the **Sentence checks** in `references/checklists.md` and against the style rules you listed in Step 0. The key question: *Would a first-time reader, having read only what is above it, understand this sentence on the first read?*
4. If anything fails, rewrite the sentence with `Edit`, then go back to step 2. If it still fails after about 3 rewrites, keep the best version, add a `TODO(sentence)` line to the notes file, and move on. The paragraph and section passes will revisit it.

### Paragraph pass (after every paragraph)
1. **Read the whole current section from the file.**
2. Apply the **Paragraph checks** in `references/checklists.md`.
3. Edit the paragraph. You may also change sentences that came before it in the section if the new paragraph shows they need it. After big changes, re-read the section once more.

### Section pass (after every section)
1. **Read the whole report from the file.**
2. Apply the **Section checks** in `references/checklists.md`.
3. Edit as needed, including earlier sections. Update the outline in the notes file if the structure changed.
4. Write the next section heading and continue.

Don't batch these passes or skip them because a sentence "is obviously fine". Doing them every time is the point of this skill. Keep it cheap by reading only the paragraph or section you need.

## Step 3: Final passes

1. **Fresh-reader pass.** Spawn a subagent with the Agent tool and give it **only the report path**: no notes, no research context. Ask it to read the report as a first-time reader in the stated audience and list every place where it got confused, had to re-read, met an undefined term, lost track of a referent, or doubted a claim. Quote each spot. Fix each spot with the sentence loop (re-reading the paragraph after each fix).
2. **Style pass.** Go through the style file rule by rule. For each rule, scan the whole report for violations and fix them.
3. **Read the whole report once more**, start to finish.
4. Delete leftover `TODO(...)` notes that are resolved. Keep the notes file unless the user asks to remove it.

## Step 4: Hand off

Tell the user where the report is, in one or two sentences on what it covers, and mention any open `TODO`s or caveats. Then offer to collect their feedback with the `style-feedback` skill. Their comments will improve this report and update the style file the next report uses.

## Revising an existing report

When asked to revise (for example, after `style-feedback`), apply the same discipline: after each changed sentence, re-read its paragraph; after each changed paragraph, re-read its section; after finishing, re-read the whole report.
