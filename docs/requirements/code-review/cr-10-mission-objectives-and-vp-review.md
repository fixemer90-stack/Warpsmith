---
title: "CR-10 — Mission, objectives and VP review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-10
tags: [requirements, code-review, atomic-review]
---

# CR-10 — Mission, objectives and VP review

**Objective:** проверить scoring, objectives, mission name normalization, Battle Ready VP.

**Files:**
- Review: `backend/state/mission.py`
- Review: `backend/engine/scenario.py`
- Review: mission/VP tests
- Output: `docs/reviews/YYYY-MM-DD/CR-10-mission-objectives-vp.md`

**Steps:**
1. Проверить mission registry and `create_mission` normalization.
2. Проверить objective placement scales with map size.
3. Проверить OC-based objective control within 3".
4. Проверить kill_points missions do not require objective scoring for VP but keep objectives for movement.
5. Проверить Battle Ready +10 VP timing.
6. Проверить winner/draw logic.
7. Запустить mission tests.

**Acceptance:** VP не остаётся 0 из-за stale objectives/mission normalization; winner вычисляется корректно.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-09/CR-10-mission-objectives-and-vp-review.md`

### Status checklist

- [x] Scope confirmed
- [x] Requirements/specs reviewed
- [x] Tests reviewed first
- [x] Production code reviewed
- [x] Correctness checked
- [x] Readability checked
- [x] Architecture checked
- [x] Security checked
- [x] Performance checked
- [x] Verification commands executed
- [x] Findings report written
- [x] Triage status updated in `docs/requirements/code-review/code-review.md`

### Result

- **Verdict:** Request Changes
- **Critical:** 2
- **Important:** 4
- **Suggestions:** 0
- **Blocked by:** —
- **Completed at:** 2026-05-09

### Report

- `docs/reviews/2026-05-09/CR-10-mission-objectives-and-vp-review.md`

### Verification

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_scenario.py tests/test_autoplay.py tests/test_result_screen.py -q
```

Result: `49 passed in 9.96s`.

## Triage summary

- [CR-10 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-10)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
