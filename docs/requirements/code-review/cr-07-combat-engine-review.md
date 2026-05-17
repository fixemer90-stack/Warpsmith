---
title: "CR-07 — Combat engine review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-07
tags: [requirements, code-review, atomic-review]
---

# CR-07 — Combat engine review

**Objective:** проверить core combat correctness: Hit → Wound → Save → Damage → FNP.

**Files:**
- Review: `backend/engine/combat.py`
- Review: `backend/engine/dice.py`
- Review: `backend/engine/modifiers.py`
- Review: `tests/test_combat*.py`, keyword tests
- Output: `docs/reviews/YYYY-MM-DD/CR-07-combat-engine.md`

**Steps:**
1. Прочитать combat tests первыми.
2. Проверить deterministic seed usage where required.
3. Проверить natural 1/6 и modifier caps.
4. Проверить weapon keyword ordering.
5. Проверить multi-weapon/multi-model aggregation.
6. Проверить AP/save/FNP interactions.
7. Запустить combat test subset.

**Acceptance:** combat math соответствует specs/tests; edge cases явно покрыты.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-07-combat-engine-review.md`

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

- **Report:** `docs/reviews/2026-05-09/CR-07-combat-engine-review.md`
- **Outcome:** Verdict: REQUEST CHANGES. Critical 3, Important 4, Suggestions 1. Natural 6 auto-wounds without Lethal Hits, Devastating Wounds bypasses all saves, AP applied twice, Sustained Hits does not add resolved hits.

## Task-03-01 Resolution (2026-05-17)

- **Natural 6 auto-wounds without Lethal Hits → FIXED.**
  - `apply_modifiers`: removed `lethal_hits` from `auto_success` group (it no longer makes hits auto-succeed).
  - `_resolve_attack_chain`: now uses `handle_critical_hit()` to determine `auto_wound` based on Lethal Hits presence, not `hit_result.is_crit` directly.
  - Updated `test_shoota_vs_marine` expected range (0.20-0.30 → 0.15-0.20) to reflect correct non-Lethal-Hits damage.
  - Added 6 new tests.
  - Full test suite: 550 passed, 3 skipped.

## Task-03-02 Resolution (2026-05-17)

- **AP applied twice → FIXED.**
  - Removed duplicate `save_target = max(1, min(6, save_target - weapon.ap))` in `_resolve_wound_chain`.
  - `defender.best_save(weapon.ap)` now applies AP exactly once; cover and modifiers apply after.
- **Devastating Wounds bypasses all saves → FIXED (partially in 3.1, completed in 3.2).**
  - `apply_modifiers`: `devastating_wounds` no longer sets `ignore_save` unconditionally — only `handle_critical_hit` sets it when the roll is a Critical Wound.
- **Ignores Cover weapon tag → FIXED.** `_resolve_wound_chain` now checks weapon modifiers for `ignore_cover` operation in addition to `context.ignores_cover`.
  - Added 9 new tests.
  - Focused tests: 44 passed.
  - Re-review full suite after replay DB reset fix: 578 passed, 3 skipped, 60 warnings (`tests/test_replay.py::test_db_init_preserves_existing_replay_rows` fixed by reopening the SQLite connection in `Database.hard_reset()`).

## Task-03-03 Resolution (2026-05-17)

- **Sustained Hits extra hits now resolve through wound/save/damage → FIXED.**
  - Removed Sustained Hits from `_roll_with_modifiers` (wrong layer — it only flipped a success flag without creating downstream attacks).
  - `_resolve_attack_chain` now uses `handle_critical_hit().extra_attacks` to spawn additional wound chains for each Sustained Hit extra hit.
  - Extra hits are normal hits (auto_wound=False), NOT Critical Hits — Lethal/Devastating Wounds do not trigger on them.
  - SH+Lethal coexistence: original crit auto-wounds, extra hits wound normally.
  - Added 6 new tests.
  - Full test suite: 578 passed, 3 skipped.

## Triage summary

- [CR-07 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-07)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.


## Phase 3 completion — Combat math

- Date: 2026-05-17
- Completed tasks: 3.1, 3.2, 3.3
- Closed findings:
  - CR-07: natural 6 / Lethal Hits semantics; AP applied exactly once; Devastating Wounds only on Critical Wounds; Sustained Hits extra hits now resolve through wound/save/damage as normal non-critical hits.
  - CR-11: AP/cover/Ignores Cover interaction regression evidence recorded; Sustained Hits closure recorded because Task 3.3 is co-owned by CR-11 in the remediation plan.
- Still open:
  - CR-07/CR-11 original review artifacts remain Request Changes until all non-Phase-3 findings are separately fixed or explicitly accepted.
- Accepted debt: none.
- Tests run:
  - `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_modifiers.py tests/test_combat*.py -q` → 50 passed in 10.38s.
  - `uv run python -m pytest tests/ -q` → 583 passed, 3 skipped, 60 warnings in 56.40s.
- Lint/format run:
  - `uv run ruff check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py` → All checks passed.
  - `uv run ruff format --check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py` → 4 files already formatted.
  - `git diff --check -- <Task 3.3 touched docs/code files>` → clean.
- Browser/API smoke evidence: none required for backend combat math phase.
- Remaining blockers before next phase: none for Phase 3 checkpoint.
