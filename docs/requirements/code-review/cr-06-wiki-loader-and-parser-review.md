---
title: "CR-06 — Wiki loader and parser review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-06
tags: [requirements, code-review, atomic-review]
---

# CR-06 — Wiki loader and parser review

**Objective:** проверить wiki-driven data loading, YAML frontmatter, no hardcode scaling risks.

**Files:**
- Review: `backend/loader/`
- Review: `backend/model/`
- Review: `wiki/`
- Review: parser/registry tests
- Output: `docs/reviews/YYYY-MM-DD/CR-06-wiki-loader-parser.md`

**Steps:**
1. Прочитать parser/registry tests.
2. Проверить YAML frontmatter как source of truth.
3. Проверить faction slug ↔ filesystem mapping.
4. Проверить unit/detachment/stratagem loading boundaries.
5. Проверить cache invalidation / stale cache risks.
6. Проверить отсутствие hardcoded faction/unit lists в code paths, где должен быть wiki/API.
7. Запустить loader-related tests.

**Acceptance:** новые faction/unit/detachment additions не требуют code changes, кроме documented exceptions.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-06-wiki-loader-and-parser-review.md`

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

#

## Result

- **Report:** `docs/reviews/2026-05-09/CR-06-wiki-loader-and-parser-review.md`
- **Outcome:** Verdict: REQUEST CHANGES. Critical 1, Important 4, Suggestions 1. Unsafe pickle cache, 168 unit files vs 160 loaded units, 27 zero-point units, 45 no-weapon units, live content validation gaps.

## Triage summary

- [CR-06 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-06)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 0.1 (runtime unit identity)

**2026-05-16.** No direct findings fixed in CR-06 scope. Structural change: `RosterState.units`
type changed (`dict` → `list`) — downstream consumers in `backend/engine/ai/autoplay.py`
and `web/routes/api_replays.py` updated. Wiki loader/parser/registry unchanged.
Full test suite: 471 passed, 0 failures.

## Regression evidence — Task 0.2 (canonical GameState serializer)

**2026-05-16.** Canonical `snapshot_game_state()` in `game_state.py`. Wiki loader/parser unchanged.
Structural cleanup: two divergent snapshot builders consolidated. 478 tests pass.
