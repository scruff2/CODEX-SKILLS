# CODEX-SKILLS

Reusable OpenAI Codex skills with workflows, references, and helper scripts for automating real-world tasks.

Each skill lives in its own top-level folder and follows the Codex skill structure:

- `SKILL.md` for the trigger description and core workflow
- `agents/openai.yaml` for UI metadata
- `scripts/` for reusable automation
- `references/` for supporting notes and implementation details

## Skills

### garmin-connect

Automates Garmin Connect workflows through the unofficial `garminconnect` Python client. The current skill focuses on safe, dry-run-first Garmin activity gear updates, including bulk-fixing missing shoe assignments on hikes and handling Garmin activity type quirks.

Folder: [`garmin-connect/`](garmin-connect/)

## Using These Skills

Copy a skill folder into your Codex skills directory, usually:

```text
~/.codex/skills/
```

Then start a new Codex session so the skill metadata can be discovered.
