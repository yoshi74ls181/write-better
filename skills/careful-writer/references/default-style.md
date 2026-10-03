# Writing style (baseline)

This baseline applies only when the user has no style file yet. The `style-feedback` skill creates the real one at `~/.claude/writing-style.md` and can start from a copy of this file.

## Reader & voice
- Default reader: a capable colleague outside this project who has not seen the research or the conversation.
- Voice: plain and direct. Use the active voice by default.
- Language/locale: follow the user's language and spelling conventions.

## Rules

### R1. Lead with the answer
- **Rule:** The opening states the main finding, recommendation, or request. Background comes after.
- **Why:** Readers often stop early, so the most important thing must come first.
- **Bad → Good:** "This report examines several factors…" → "Switching to X cuts build time by 40%; the rest of this note explains why."
- **Source:** baseline

### R2. Define before use
- **Rule:** Define every acronym, symbol, and specialist term at its first use, or don't use it.
- **Why:** The reader has not seen the research notes.
- **Bad → Good:** "The ELBO dropped." → "The evidence lower bound (ELBO), the quantity the model maximizes, dropped."
- **Source:** baseline

### R3. Say how sure you are, once
- **Rule:** State the confidence and the evidence for each claim plainly. Don't stack hedges ("may possibly suggest").
- **Why:** Stacked hedges hide how strong the evidence actually is.
- **Bad → Good:** "This might perhaps indicate a possible link." → "Two of three datasets show the link; the third is too small to tell."
- **Source:** baseline

### R4. Prefer the concrete
- **Rule:** Use numbers, names, and examples instead of vague quantifiers ("significant", "various", "many").
- **Why:** Vague words make the reader guess.
- **Bad → Good:** "Performance improved significantly." → "Latency fell from 120 ms to 45 ms."
- **Source:** baseline

### R5. No throat-clearing
- **Rule:** Cut openers like "It is important to note that" and "It should be mentioned that".
- **Why:** They delay the point and add nothing.
- **Bad → Good:** "It is worth noting that the API is rate-limited." → "The API is rate-limited."
- **Source:** baseline

### R6. Name what "this" refers to
- **Rule:** Follow "this", "that", and "these" with a noun when the referent could be unclear.
- **Why:** A bare "this" often points to something the reader can't identify.
- **Bad → Good:** "This causes problems." → "This retry loop causes problems."
- **Source:** baseline
