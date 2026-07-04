---
name: garmin-connect
description: Work with Garmin Connect automation through the unofficial garminconnect Python client, especially auditing and bulk-fixing activity gear assignments such as shoes on hikes. Use when Codex needs to inspect Garmin Connect activities or gear, handle token-based Garmin login/MFA, update missing activity gear with dry-run-first safeguards, or troubleshoot Garmin activity type mismatches such as hikes returned as type "other".
---

# Garmin Connect

## Core Rules

- Treat Garmin Connect write operations as live production changes. Run a dry run first, show the exact activities that would change, and ask for confirmation before using `--apply`.
- State clearly that the workflow uses unofficial/private Garmin Connect endpoints via the `garminconnect` Python package, not a Garmin-supported public API.
- Never ask the user to paste Garmin passwords into chat. Prefer interactive local prompts, `GARMIN_EMAIL`/`GARMIN_PASSWORD` environment variables, or cached tokens under `~/.garminconnect`.
- Expect Garmin rate limits and fragile response shapes. Use conservative paging and sleeps between writes.
- Do not assume Garmin's activity type filter works for hikes. Some accounts expose hikes as type `other` with activity names containing `Hike`; fetch broad activity pages and filter locally when needed.

## Gear Update Workflow

Use `scripts/update_activity_gear.py` for bulk gear assignment tasks.

1. Install dependencies if needed:

```powershell
python -m pip install garminconnect curl_cffi
```

2. Run a dry run using a gear name or UUID:

```powershell
python path\to\update_activity_gear.py --gear-name "Columbia" --activity-name-fragment "hike"
```

3. Review the output:

- selected gear name and UUID
- inferred or explicit date window
- number of matching activities
- number already linked
- exact activities that would update

4. Apply only after user confirmation:

```powershell
python path\to\update_activity_gear.py --gear-name "Columbia" --activity-name-fragment "hike" --apply
```

5. Verify with another dry run. A successful verification should report `Would update: 0`.

## Date Windows

For "same shoe since it was first used" rules, omit `--start-date`. The script first tries Garmin gear history to infer the earliest dated activity linked to the selected gear. If Garmin cannot provide a usable gear history, pass an explicit date:

```powershell
python path\to\update_activity_gear.py --gear-name "Columbia" --start-date 2025-07-19
```

Use `--end-date YYYY-MM-DD` when the update should stop before today. Otherwise the script defaults to the current local date.

## Authentication

- The script caches tokens in `~/.garminconnect`.
- Use `--force-login` when cached tokens are stale or Garmin rejects them.
- If running commands from Codex in a sandboxed environment, Garmin network calls may need escalation/approval.
- Garmin may return `429` for rate-limited login attempts. Wait before retrying and prefer cached tokens after a successful login.

## Troubleshooting

- `Fetched 0 total hiking activities`: Garmin may not label hikes as `hiking`. Use `--activity-name-fragment "hike"` or inspect recent activities for their names/types.
- `Could not infer a start date`: no dated activity is linked to the selected gear. Re-run with `--start-date`.
- `Multiple gear items matched`: use `--gear-uuid` or a more specific `--gear-name`.
- `Failed to retrieve social profile`: token cache may be stale, the sandbox may block network access, or Garmin rejected the session. Try `--force-login`; if Codex is running the command, rerun with network approval.

Read `references/session-notes.md` when troubleshooting activity type mismatches or reconstructing the gear-update pattern from the original successful run.
