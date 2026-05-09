---
title: "CR-24 — Final integration regression gate"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-24
tags: [requirements, code-review, atomic-review]
---

# CR-24 — Final integration regression gate

**Objective:** финально подтвердить, что review/fix cycle не сломал продукт.

**Files:**
- Scope: whole repo
- Output: `docs/reviews/YYYY-MM-DD/CR-24-final-regression-gate.md`

**Steps:**
1. Выполнить `uv run ruff check .`.
2. Выполнить `uv run ruff format --check .`.
3. Выполнить `node -c web/static/team_builder.js`.
4. Выполнить `node -c web/static/scenario_setup.js`.
5. Выполнить `node -c web/static/battlefield_map.js`.
6. Выполнить `uv run python -m pytest tests/ -q`.
7. Запустить server без reload и проверить `/api/health`.
8. Browser smoke key pages: `/`, `/team-builder`, `/scenario-setup`, `/my-rosters`, `/result/<known_or_generated_game_id>` if available.
9. Записать final verdict and remaining accepted debt.

**Acceptance:** final gate report создан; release readiness verdict explicit.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-24-final-integration-regression-gate.md`

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
