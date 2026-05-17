# Review — Task 1.4 / Phase 1

Date: 2026-05-17
Task: `docs/remediation/task-01-04-emit-canonical-json-artifacts.md`
Scope: Task 1.4 implementation and Phase 1 completion readiness.

## Verdict

REQUEST CHANGES.

Task 1.4 is marked completed in the task file, but the implementation does not satisfy the canonical artifact/registry contract, and Phase 1 is not ready to close.

## Checks run

- `uv run python -m pytest tests/test_content_contracts.py -q`
  - First run before recompiling generated artifacts: FAILED, 1 failed / 22 passed.
  - Failure: `test_compiler_produces_units_json` saw stale `units/index.json` with only 1 unit.
- `uv run python - <<'PY' ... CanonicalContentRegistry/WikiRegistry smoke ... PY`
  - `CanonicalContentRegistry.load()` returned `False`.
  - `WikiRegistry.load(use_cache=True)` logged JSON-cache import failure and fell back to raw wiki parse.
- `uv run python -m pytest tests/test_content_contracts.py tests/test_registry.py -q`
  - FAILED, exit 4: `tests/test_registry.py` does not exist.
- `uv run ruff check backend/loader tests/test_content_contracts.py`
  - FAILED, 6 lint errors.
- `uv run ruff format --check backend/loader tests/test_content_contracts.py`
  - FAILED, 2 files would be reformatted.
- `git diff --check -- backend/loader/compiler.py backend/loader/schema.py backend/loader/registry.py tests/test_content_contracts.py docs/remediation/task-01-04-emit-canonical-json-artifacts.md docs/remediation/remediation-plan.md data/generated/content`
  - FAILED: CRLF/trailing whitespace in `backend/loader/registry.py`.
- `compile_content(freeze_clock='2026-01-01T00:00:00+00:00')`
  - Produced 15 artifacts / 160 units after manual recompilation, but still with one dangling-ref collision.

## Findings

### Critical 1 — `CanonicalContentRegistry` cannot load generated content

`backend/loader/registry.py:373-378` loads `faction_units/index.json`, then builds shard paths as:

```python
shard_file = self._dir / "faction_units" / Path(entry["file"])
```

But `entry["file"]` already contains `faction_units/<slug>.json`, so the runtime path becomes:

```text
data/generated/content/faction_units/faction_units/adeptus-mechanicus.json
```

Observed result:

```text
CanonicalContentRegistry.load() False
Failed to load canonical content: .../faction_units/faction_units/adeptus-mechanicus.json
```

This directly violates Task 1.4 acceptance criteria:

- `CanonicalContentRegistry` loads every canonical object kind from generated JSON.
- Registry exposes faction availability through `faction_units` links.
- Registry load validates required artifacts/references.

Required fix:

- Resolve shard paths relative to `self._dir`, not `self._dir / "faction_units"` when index entries already include the directory.
- Add a regression test that constructs `CanonicalContentRegistry`, calls `load()`, asserts `True`, and verifies non-empty `factions`, `units`, `faction_units`, `weapons`, `detachments`, `stratagems`, `enhancements`, `rules`.

### Critical 2 — `WikiRegistry` JSON cache path is broken and falls back to raw wiki parsing

`backend/loader/registry.py:210-217` imports `load_units_from_json`, but `backend/loader/compiler.py` no longer defines it. The current helper is `load_all_units`.

Observed result:

```text
Failed to load JSON artifacts: cannot import name 'load_units_from_json' ... — falling back to parse
```

This means runtime content loading does not reliably consume generated JSON. It silently falls back to raw wiki parse and recompiles.

This violates Phase 1 checkpoint:

- runtime loaders can rely on `CanonicalContentRegistry`/generated JSON instead of raw wiki reads.
- no unsafe/stale cache risk.

Required fix:

- Update `_load_from_json_cache()` to use the sharded loader (`load_all_units`) or the canonical registry.
- Convert canonical unit records back into runtime `Unit` objects intentionally, not by passing raw canonical fields into `Unit(**data)` with broad fallback.
- Add a test that fails if cache load falls back to `_scan_and_parse()` when fresh generated artifacts exist.

### Critical 3 — Dangling references are detected but compilation still succeeds

`compile_content()` reports a dangling ref:

```text
{'kind': 'dangling_ref', 'field': 'detachment.faction_id', 'id': 'detachment:core:detachments-index', 'ref': 'faction:core'}
```

But compilation still writes artifacts and Task 1.4 is marked complete.

This violates the task contract:

- dangling cross-artifact references MUST fail compilation.
- compiler writes generated artifacts atomically: validate everything first, then replace generated files.
- failed compilation must not leave partially updated generated artifacts.

Required fix:

- Separate non-fatal duplicate display-name collision reports from fatal validation errors.
- Fatal dangling refs and duplicate canonical ids must raise before replacing existing generated artifacts.
- Add tests for `unit.faction_id`, `detachment.faction_id`, `faction_units` keys, and `faction_units.available_unit_ids` dangling refs.

### Important 1 — Manifest does not list `manifest.json` inside the written manifest

`backend/loader/compiler.py:526-529` writes `manifest.json`, then appends a `ManifestEntry(filename="manifest.json", ...)` to the in-memory `manifest.artifacts`, but does not rewrite the file afterward.

Observed generated `manifest.json`:

```text
manifest artifact count 14
has manifest False
```

Task 1.4 requires `manifest.json` to list every emitted top-level artifact and shard with hashes. The current on-disk manifest omits itself.

Required fix:

- Either explicitly decide that `manifest.json` is excluded from self-hashing and update the task contract, or write a stable manifest entry strategy and test it.
- Add a manifest hash test that validates every listed file exists and every listed hash matches file bytes.

### Important 2 — Unit records do not include `weapon_ids`, and weapon references are not validated

`backend/loader/compiler.py:209-237` embeds `ranged_weapons`/`melee_weapons` directly in unit records.
`backend/loader/compiler.py:253-258` separately creates `weapons.json` records, but unit records do not store `weapon_ids`.

This violates:

- Unit records include `weapon_ids` where applicable.
- Dangling `unit.weapon_ids -> weapons.json` references fail compilation.

Required fix:

- Generate stable weapon ids first.
- Store `weapon_ids` on each unit record.
- Validate every `unit.weapon_ids` entry exists in `weapons.json`.
- Add regression tests for a missing weapon reference.

### Important 3 — Canonical ids are derived from display name/source faction; explicit `canonical_id` is ignored

`backend/loader/compiler.py:138-139` creates unit ids from `name` and `faction`:

```python
return f"unit:{self._slug(faction)}:{self._slug(name)}"
```

The compiler does not read/use frontmatter `canonical_id`, and unit `source_path` is written as an empty string at `backend/loader/compiler.py:213`.

This violates:

- Canonical ids are independent from display names/source file paths.
- Canonical ids survive display/source-path changes when explicit `canonical_id` is present.
- Unit records include `source_path`.

Required fix:

- Parse explicit `canonical_id` from frontmatter and make it authoritative.
- Preserve source path in canonical records.
- Add tests for display-name rename and source-file rename with unchanged explicit canonical id.

### Important 4 — Tests do not cover the Task 1.4 acceptance criteria

Only `tests/test_content_contracts.py` references compiler helpers. No tests currently reference `CanonicalContentRegistry` or `faction_units`.

Observed scan:

```text
test_content_contracts.py: ['compile_content', 'load_units_index', 'deterministic']
(no tests for CanonicalContentRegistry/faction_units)
```

Missing required coverage:

- duplicate canonical ids across shards fail compilation.
- duplicate display names emit a collision report but remain valid.
- dangling references fail compilation.
- renamed source files and display-name changes with explicit `canonical_id`.
- deterministic rebuild output and manifest shard hashes.
- registry loading sharded unit definitions as one logical `units` collection.
- faction availability resolving shared units.
- shared/common units not duplicated into subfaction definition shards.

Required fix:

- Add focused Task 1.4 tests using temporary wiki/output dirs.
- Tests must compile from input fixtures, not depend on whatever happens to be in `data/generated/content`.

### Important 5 — Generated artifact tests depend on pre-existing mutable repository state

Before manual recompilation, `tests/test_content_contracts.py::test_compiler_produces_units_json` failed because `data/generated/content/units/index.json` contained only one unit. After running `compile_content(...)`, the same test passed.

That means the test does not build its own deterministic fixture and can pass/fail depending on local generated files.

Required fix:

- Use `tmp_path` output dir and compile during the test setup.
- Avoid writing test-generated artifacts into repository `data/generated/content` unless explicitly regenerating checked-in artifacts.

### Important 6 — `git diff --check`, ruff check, and format check do not pass

Observed:

- `git diff --check` fails on CRLF/trailing whitespace in `backend/loader/registry.py`.
- `uv run ruff check backend/loader tests/test_content_contracts.py` fails with 6 issues.
- `uv run ruff format --check backend/loader tests/test_content_contracts.py` fails; `backend/loader/schema.py` and `tests/test_content_contracts.py` would be reformatted.

This contradicts Task 1.4 verification claims:

- `uv run ruff check backend/loader/` — All checks passed.
- `uv run ruff format --check backend/loader/` — Already formatted.
- `git diff --check` passes.

Required fix:

- Normalize touched files to LF.
- Fix ruff issues or explicitly document justified ignores.
- Re-run and record exact passing outputs.

### Important 7 — Phase 1 source plan and phase metadata are stale

Current state:

```text
remediation-plan Phase1 unchecked: 57
remediation-plan Phase1 checked: 0
triage-summary Phase 1 complete present: False
code-review.md Phase 1 complete present: False
```

`task-01-04` claims Phase 1 complete, but the source plan and required metadata surfaces are not updated.

This violates Phase completion artifact rules in `docs/remediation/remediation-plan.md` and the Warpsmith remediation workflow.

Required fix:

- Do not mark Phase 1 complete until implementation and verification pass.
- After fixes, sync:
  - `docs/remediation/remediation-plan.md`
  - `docs/reviews/2026-05-10/triage-summary.md`
  - affected CR artifacts: CR-06, CR-11, CR-12, CR-21
  - `docs/requirements/code-review/code-review.md`

## Phase 1 readiness

Not ready.

Tasks 1.1-1.3 are marked completed in their task files, but source-plan checkboxes remain stale. Task 1.4 is currently the blocker: canonical generated artifacts exist after manual compile, but registry loading, cache loading, fatal validation semantics, manifest completeness, tests, lint/format, and phase documentation are not acceptable yet.

## Required re-check after fixes

Minimum commands before marking Task 1.4 / Phase 1 complete:

```bash
sed -i 's/\r$//' backend/loader/registry.py backend/loader/compiler.py backend/loader/schema.py tests/test_content_contracts.py
uv run python -m pytest tests/test_content_contracts.py -q
uv run python -m pytest tests/ -q
uv run ruff check backend/loader tests/test_content_contracts.py
uv run ruff format --check backend/loader tests/test_content_contracts.py
git diff --check -- backend/loader/compiler.py backend/loader/schema.py backend/loader/registry.py tests/test_content_contracts.py docs/remediation/task-01-04-emit-canonical-json-artifacts.md docs/remediation/remediation-plan.md data/generated/content
```

Also add/restore the documented registry test target or update the verification command if `tests/test_registry.py` is intentionally not used.
