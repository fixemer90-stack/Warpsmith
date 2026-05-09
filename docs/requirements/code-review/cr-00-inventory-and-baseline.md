---
title: "CR-00 — Inventory and baseline"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-00
tags: [requirements, code-review, atomic-review]
---

# CR-00 — Inventory and baseline

**Objective:** зафиксировать живое состояние проекта до review, чтобы отличать реальные проблемы от stale docs.

**Files:**
- Read: `pyproject.toml`
- Read: `main.py`
- Read: `DEV_INDEX.md`
- Read: `AGENTS.md`
- Read: `docs/features/Features_index.md`
- Output: `docs/reviews/YYYY-MM-DD/CR-00-inventory-baseline.md`

**Steps:**
1. Выполнить `git status --short` и зафиксировать pre-existing modified files.
2. Выполнить `git branch --show-current`.
3. Посчитать Python/JS/HTML/MD files по директориям.
4. Выполнить `uv run python -m pytest --collect-only -q`.
5. Выполнить `uv run ruff check .`.
6. Выполнить `uv run ruff format --check .`.
7. Выполнить `node -c` для всех JS-файлов из `web/static/*.js`.
8. Сохранить baseline: test count, lint status, known warnings.

**Acceptance:** baseline report создан; есть список scope-директорий и команд проверки.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-00-inventory-and-baseline.md`

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
