---
title: "CR-06 — Wiki loader and parser review"
status: request-changes
review_task: CR-06
date: 2026-05-09
source: ../../requirements/code-review/cr-06-wiki-loader-and-parser-review.md
---

# CR-06 — Wiki loader and parser review

## Verdict

REQUEST CHANGES / CONTENT LOADER HARDENING REQUIRED

The wiki/frontmatter loader works well enough for current smoke/API tests, but it is not yet safe or complete enough as the canonical source of faction/unit data. The highest-risk issue remains unsafe cache deserialization via `pickle.load`, already surfaced by CR-02 and confirmed here in the loader path. Data completeness also has visible gaps: 168 unit markdown files exist under `wiki/units`, but only 160 units are loaded by the registry; 27 loaded units still have 0 points and 45 loaded units have no parsed weapons.

## Scope inspected

- `backend/loader/parser.py`
- `backend/loader/registry.py`
- `backend/loader/schema.py`
- `backend/model/unit.py`
- `tests/test_parser.py`
- `tests/test_unit.py`
- `tests/test_faction_browser.py`
- `tests/test_detachment_picker.py`
- `wiki/**/*.md` frontmatter parse scan
- registry live load from `/mnt/d/Python/Balthier/simulator/wiki`

## Verification commands

```text
uv run python -m pytest tests/test_parser.py tests/test_unit.py tests/test_faction_browser.py tests/test_detachment_picker.py -q
```

Result:

```text
40 passed, 1 skipped in 2.74s
```

Registry/content inventory script result:

```text
UNITS 160
DETACHMENTS 23
FACTIONS 3 ['adeptus-mechanicus', 'orks', 'tau']
FILES_TRACKED_MTIME 183
NO_WEAPONS 45
ZERO_POINTS 27
BAD_SQUAD 0
CHAR_WARLORDS 50 of 50
DUP_UNIT_NAMES []
DET_BY_FACTION [('orks', 10), ('adeptus-mechanicus', 7), ('tau', 5), ('core', 1)]
```

Frontmatter parse scan:

```text
WIKI_MD_TOTAL 467
FRONTMATTER_ERRORS 0 []
EMPTY_METADATA_UNITS_DETACH 0 []
UNIT_FILES 168
DETACHMENT_FILES 23
```

Unit-file/load mismatch scan:

```text
UNIT_FILES 168 LOADED_UNITS 160 MISSING_BY_STEM 10
['mechanicus/Corpuscarii Electropriests.md', 'mechanicus/Fulgurite Electropriests.md', 'orks/Dakka.md', 'orks/Killsaw.md', 'orks/Kustom Force Field.md', 'orks/Makari.md', 'orks/Nob on Smasha Squig.md', 'orks/Power Klaw.md', 'orks/Snazzgun.md', 'tau/Smart Missile System.md']
```

## Findings

### Critical: unsafe pickle cache deserialization in wiki registry

Evidence:

- `backend/loader/registry.py` uses `pickle.load` for registry cache.
- Cache file is outside the immutable source content model and can be tampered with locally or by a compromised deployment volume.

Risk:

- Arbitrary code execution on process startup/load if the cache file is malicious.
- This is especially risky because the loader is used as global application data and could be hit by API/page requests.

Required change:

- Replace pickle cache with a safe format, preferably JSON with explicit schema/version.
- If cache is kept, include schema version, source file mtimes/hash, and robust invalidation.
- Add a regression test that a malformed cache does not execute code and falls back to a rebuild.

### Important: loaded unit count does not match unit markdown file count

Evidence:

- `wiki/units/**/*.md`: 168 files.
- Registry loaded units: 160.
- Missing-by-stem list includes entries such as `orks/Dakka.md`, `orks/Killsaw.md`, `orks/Snazzgun.md`, and `tau/Smart Missile System.md`.

Interpretation:

- Some files under `wiki/units` appear to be wargear-like records or duplicate naming variants rather than loadable units.
- The loader currently does not produce an explicit skipped-file report, so reviewers cannot distinguish expected non-unit content from parser loss.

Required change:

- Add loader diagnostics: loaded, skipped, skipped_reason, parse_errors.
- Move non-unit/wargear files out of `wiki/units` or mark them with explicit `type: wargear` and skip intentionally.
- Make `registry.load()` expose a reviewable warning summary.

### Important: 27 loaded units have 0 points

Evidence sample:

```text
['Attack Fighta', 'Big Gunz', 'Big Mek on Warbike', 'Big Mek with Kustom Force Field', 'Boss Zagstruk', 'Chinork Warkopta', 'Da Red Gobbo', 'Deff Rolla Battle Fortress', 'Deffkoptas with Big Shootas', 'Fighta-Bommer', 'Grot Bomm Launcha', 'Grot Mega-Tank', 'Grot Tanks', 'Kannonwagon', 'Kaptin Badrukk']
```

Risk:

- Team Builder and roster generation can create underpriced/invalid lists.
- Commercial product trust is damaged if points are silently wrong.

Required change:

- Enforce explicit status for 0-point units: `legendary`, `unsupported`, `needs_points`, or excluded from roster generation.
- Add tests that generator does not use `needs_points`/unsupported entries.
- Add a content validation command that fails CI if production-loadable units have unexpected `points <= 0`.

### Important: 45 loaded units have no parsed weapons

Evidence sample:

```text
['Archaeopter Fusilave', 'Archaeopter Stratoraptor', 'Archaeopter Transvector', 'Belisarius Cawl', 'Corpuscarii Electro-priests', 'Cybernetica Datasmith', 'Fulgurite Electro-priests', 'Ironstrider Ballistarii', 'Kastelan Robots', 'Kataphron Breachers', 'Kataphron Destroyers', 'Onager Dunecrawler', 'Pteraxii Skystalkers', 'Pteraxii Sterylizors', 'Serberys Raiders']
```

Risk:

- Combat simulation falls back to placeholder/default weapon paths elsewhere.
- Unit cards may appear valid but produce unrealistic simulation behavior.

Required change:

- Treat missing weapons as a validation warning/error depending on unit category.
- Add explicit support for non-combat support units if some should truly have no weapons.
- Block auto-generation/simulation for units with no weapon profile unless an explicit fallback is accepted by requirements.

### Important: test suite allows wiki parser smoke to skip on missing wiki

Evidence:

- `tests/test_detachment_picker.py::TestRegistryDetachmentSupport.test_registry_detachments_loaded` catches exceptions and calls `pytest.skip`.

Risk:

- Loader regressions can be hidden in CI if path/config changes.
- CR-06 requires content integrity, not just API smoke.

Required change:

- Add a dedicated content validation test/command that must run when wiki is present in repo.
- Keep unit-level parser tests separate from live content validation.

### Suggestion: hardcoded faction-specific AI comments/examples are acceptable but should not become loader source of truth

Evidence:

- Static scan found only example/comment occurrences in backend production code, not hardcoded faction lists for the browser/loader.
- API/page faction lists appear loader-driven.

Recommendation:

- Keep UI/API faction lists sourced from registry.
- If faction-specific AI profiles grow, define them as data/config with fallback, not scattered code constants.

## Positive notes

- All 467 wiki markdown files parsed as frontmatter with no frontmatter exceptions.
- All loaded units have valid `squad_size` dict shape.
- Duplicate loaded unit names were not found.
- All 50 loaded Character-like units are marked `can_be_warlord`.
- Public faction/detachment browser smoke tests pass.

## Required follow-up before approval

1. Replace pickle cache with safe JSON/schema cache or disable cache in production.
2. Add loader diagnostics and CI-facing content validation.
3. Classify/clean the 168 unit files vs 160 loaded unit discrepancy.
4. Resolve or explicitly mark the 27 zero-point units.
5. Resolve or explicitly mark the 45 no-weapon units.
6. Add non-skipping tests for live wiki content integrity when wiki exists in repo.

## Status update

CR-06 remains request-changes.
