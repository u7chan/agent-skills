---
name: skill-creator
description: >
  Use this skill when creating or improving a SKILL.md file.
  Activate when told "create a skill", "write a SKILL.md", or "turn this workflow into a skill",
  or when asked to review or improve an existing skill.
---

# Overview

This skill is for designing, creating, and improving other skills (SKILL.md files).
Identify which stage the user is at and begin assistance from the appropriate step.

---

# When to Use This Skill

- When told "I want to create a skill" or "please write a SKILL.md"
- When told "turn this workflow into a skill" (extract the workflow from conversation history)
- When asked to review or improve an existing SKILL.md

---

# What the Agent Does

1. Listen to the user's intent and goals
2. Generate a draft SKILL.md following the "Creation Steps" below
3. Self-verify using the quality checklist
4. Output the result as a file

---

# Directory Structure

Create skills with the following structure. Only SKILL.md is required; add others as needed.

    my-skill/
    ├── SKILL.md          # Main instruction file (required)
    ├── reference.md      # Large specs, schemas, or glossaries (split out if content gets long)
    ├── examples.md       # Concrete input/output examples (split out if 3+ examples)
    └── scripts/          # Validation or transformation scripts (only if external tools are needed)
        └── validate.py

## File Split Criteria

- If the main content exceeds 200 lines, move details to `reference.md`
- If there are 3 or more input/output examples, split them into `examples.md`
- If the process uses external APIs or libraries, place scripts under `scripts/`

---

# SKILL.md Format

## Front Matter

Include the following at the top of the file.

    ---
    name: unique identifier for the skill (e.g., pdf-summarizer)
    description: >
      Describe what this skill does and when it should activate in 1–3 sentences.
      Write trigger conditions specifically, such as "when told X" or "when given a Y file".
    ---

**Rules for `name`:**
- Maximum 64 characters
- Only lowercase letters, numbers, and hyphens
- Do not use strings reserved for XML tags
- Do not use reserved words (e.g., `anthropic`, `claude`, or other engine-specific terms)
- Name using a verb or noun phrase (e.g., `invoice-parser`, `slide-creator`)

**Rules for `description`:**
- Required — do not omit
- Maximum 1024 characters
- Do not use strings reserved for XML tags
- Must include both what the skill does (function) and when to use it (trigger)
- Do not use vague language ("appropriately", "properly", "as needed")

## Body Structure

Write the body in the following section order. Omit sections that are not needed.

1. **Overview** — Describe the problem this skill solves in 1–2 sentences
2. **When to Use This Skill** — List trigger conditions as bullet points
3. **What the Agent Does** — List execution steps as numbered items (avoid vague verbs)
4. **Input and Output** — Explicitly state what is received and what is produced
5. **Step Details** — Describe concrete operations for each step
6. **Quality Check** — List completion criteria and verification points
7. **References** — List paths to related files (if any)

---

# Creation Steps

## Step 1: Gather Intent

If the conversation history contains a workflow, extract the following from it.
If not, ask the user directly.

- The problem or goal the skill should solve
- Typical input (files, text, URLs, etc.)
- Expected output (file format, content)
- Main processing steps

## Step 2: Generate Draft

Using the gathered information, generate a SKILL.md following the format above.
Follow these rules when writing steps:

- Use imperative form consistently ("do X", "write Y", "ensure Z")
- 1 step = 1 action — do not pack multiple operations into one line
- Add warnings for steps that are prone to errors

## Step 3: Quality Check

Self-verify the generated SKILL.md on the following points.

- [ ] Can you tell when to use it just by reading `description`?
- [ ] Can you produce the output by following the steps from top to bottom?
- [ ] Are there no vague expressions ("appropriately", "properly", "as needed") in the steps?
- [ ] Are input and output explicitly stated?
- [ ] Are there no nested code blocks? (Use indentation as an alternative for format examples)

## Step 4: Output

Save the completed SKILL.md to the specified path and present it to the user.
If no path is specified, save it under `outputs/`.

---

# Common Failure Patterns

Avoid the following anti-patterns.

**Description is too abstract**
- Bad: `This skill processes documents`
- Good: `Activates when a PDF is provided or when told "summarize this", and generates a summary in English`

**Steps are vague**
- Bad: `Format it appropriately`
- Good: `Use H2 (##) for headings and limit bullet point nesting to 2 levels`

**Nested code blocks**
- Writing code blocks (triple backticks) inside SKILL.md will conflict with outer code blocks
- Instead, use indentation (4 spaces) to show code examples

---

# References

- `examples.md` — Good and bad examples of SKILL.md (if available)
- `reference.md` — Detailed front matter specification (if available)
