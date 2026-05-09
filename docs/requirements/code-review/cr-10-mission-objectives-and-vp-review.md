---
title: "CR-10 — Mission, objectives and VP review"
parent: code-review
status: pending
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

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-10-mission-objectives-and-vp-review.md`

### Status checklist

- [ ] Scope confirmed
- [ ] Requirements/specs reviewed
- [ ] Tests reviewed first
- [ ] Production code reviewed
- [ ] Correctness checked
- [ ] Readability checked
- [ ] Architecture checked
- [ ] Security checked
- [ ] Performance checked
- [ ] Verification commands executed
- [ ] Findings report written
- [ ] Triage status updated in `docs/requirements/code-review/code-review.md`

### Result

- **Verdict:** Not started
- **Critical:** 0 known before execution
- **Important:** 0 known before execution
- **Suggestions:** 0 known before execution
- **Blocked by:** —
- **Completed at:** —
