---
title: "CR-00 — Inventory and baseline"
parent: code-review
status: approved
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

**Status:** Approved

**Review report:** `docs/reviews/2026-05-09/CR-00-inventory-and-baseline.md`

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

- **Verdict:** APPROVE / BASELINE CAPTURED
- **Critical:** 0
- **Important:** 0
- **Suggestions:** 4 baseline risks/next-review notes
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-09/CR-00-inventory-and-baseline.md`
- **Completed at:** 2026-05-09

## Triage summary

- [CR-00 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-00)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
