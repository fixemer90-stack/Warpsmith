---
title: "CR-14 — Autoplay, replay and result review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-14
tags: [requirements, code-review, atomic-review]
---

# CR-14 — Autoplay, replay and result review

**Objective:** проверить full simulation pipeline: setup → auto-play → replay storage → result summary.

**Files:**
- Review: `backend/engine/ai/autoplay.py`
- Review: `backend/engine/replay.py`
- Review: `web/routes/api_replays.py`
- Review: `web/static/scenario_setup.js`
- Review: `web/static/replay_viewer.js`
- Review: `web/static/result_chart.js`
- Output: `docs/reviews/YYYY-MM-DD/CR-14-autoplay-replay-result.md`

**Steps:**
1. Проверить game_id serialization and redirect flow.
2. Проверить replay persistence JSON columns.
3. Проверить `_snapshot_state` includes units, positions, VP, map dimensions.
4. Проверить `_build_summary` parsing kills/damage/charges.
5. Проверить result winner fallback.
6. Проверить round viewer dynamic grid size.
7. Запустить replay/result tests and one TestClient E2E auto-play.

**Acceptance:** generated/saved rosters can run simulation and open `/result/{game_id}` with meaningful summary.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-14-autoplay-replay-and-result-review.md`

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
