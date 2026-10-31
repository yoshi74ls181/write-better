# Writing style (baseline)

This baseline applies only when the user has neither a rules repository nor a style file. The `doc-feedback` skill creates the real one at `~/.claude/writing-style.md` and can start from a copy of this file.

## Reader & voice
- Default reader: a capable colleague outside this project who has not seen the research or the conversation.
- Voice: plain and direct. Use the active voice by default.
- Language/locale: follow the user's language and spelling conventions.

## Rules

### R1. Lead with the answer

The opening states the main finding, recommendation, or request. Background comes after.

- Bad → Good: "This report examines several factors…" → "Switching to X cuts build time by 40%; the rest of this note explains why."

### R2. Define before use

Define every acronym, symbol, and specialist term at its first use, or don't use it.

- Bad → Good: "The ELBO dropped." → "The evidence lower bound (ELBO), the quantity the model maximizes, dropped."

### R3. Say how sure you are, once

State the confidence and the evidence for each claim plainly. Don't stack hedges ("may possibly suggest").

- Bad → Good: "This might perhaps indicate a possible link." → "Two of three datasets show the link; the third is too small to tell."

### R4. Prefer the concrete

Use numbers, names, and examples instead of vague quantifiers ("significant", "various", "many").

- Bad → Good: "Performance improved significantly." → "Latency fell from 120 ms to 45 ms."

### R5. No throat-clearing

Cut openers like "It is important to note that" and "It should be mentioned that".

- Bad → Good: "It is worth noting that the API is rate-limited." → "The API is rate-limited."

### R6. Name what "this" refers to

Follow "this", "that", and "these" with a noun when the referent could be unclear.

- Bad → Good: "This causes problems." → "This retry loop causes problems."

### R7. One idea per sentence

Give each sentence one idea, with its subject and verb early. When there is more to say than fits plainly, leave out the less-important facts. Don't pack them in as inserted clauses, qualifiers and colon lists.

- Bad → Good: "So that the job never fills the disk, no run starts while the volume's usage, as df reports it, is at or above a limit you set, and a run that reaches it is stopped." → "A limit keeps the job from filling the disk. No run starts while the disk is fuller than the limit. A running job stops when it reaches the limit."

### R8. The reader does what the reader does

When the reader performs an action, make "you" the subject. Make a tool, a file or a setting the subject only of what it does by itself.

- Bad → Good: "The wake browser changes both limits." → "You can change these limits in the wake browser."
