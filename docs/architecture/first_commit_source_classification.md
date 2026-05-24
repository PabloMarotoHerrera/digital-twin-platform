# First Commit Source Classification

Date: 2026-05-24

Scope: review and classification only. This document prepares a first real project commit plan after `.gitignore` was updated to expose `source/apps` and `source/extensions`. No staging, commit, push, cleanup, source edits, or generated-directory changes were performed.

## 1. Current Git State Summary

Observed `git status --short` before writing this document:

```text
 M .gitignore
 M premake5.lua
 M repo.toml
?? 00_PROJECT_CONTEXT.txt
?? 01_RULES_AND_LIMITATIONS.txt
?? 02_TASKS_BACKLOG.txt
?? 03_USD_CONVENTIONS.txt
?? 04_CODEX_WORKFLOW.txt
?? 05_MIGRATION_MAP.txt
?? 06_EXTENSION_PLAYBOOK.txt
?? 07_PROFESIONAL_VISUALIZATION.txt
?? CustomPrimitiveMesh.zip
?? current_repository_analysis.md
?? digital_twin_contexto_maestro.md
?? docs/
?? source/
```

Important notes:

- `source/` is now visible because Ticket 003 removed the broad `/source` ignore.
- `git ls-files source` returned no tracked source files, so all current `source/apps` and `source/extensions` content is new to Git.
- Generated dumps such as `repo_tree.txt`, `source_tree.txt`, `tools_tree.txt`, `important_files.txt`, `extensions_list.txt`, `source/source_tree.txt`, and `templates/templates_tree.txt` are now ignored by `.gitignore`.
- Source-local `__pycache__` and `.pyc` files exist physically but are ignored by root and/or extension-level ignore rules.

## 2. Classification Legend

- `must-track in first commit`: required for the app to be represented as a product repo.
- `should-track in first commit`: important supporting source/docs for the first commit.
- `optional / owner decision`: likely useful, but ownership/location/purpose needs confirmation.
- `should-not-track`: should not be in the first commit.
- `should-ignore`: generated/cache/vendor/runtime content that should remain ignored.
- `unknown / needs review`: not enough evidence to classify safely.

## 3. Modified Tracked Files

| Path | Classification | First commit recommendation | Rationale |
| --- | --- | --- | --- |
| `.gitignore` | must-track in first commit | Include | Required hygiene fix from Ticket 003. It exposes product source while preserving Kit generated/runtime ignores and generated dump ignores. |
| `premake5.lua` | must-track in first commit | Include if the first commit includes `source/apps/my_own_software.kit` | Adds `define_app("my_own_software.kit")`, which connects the product app descriptor to the Kit build/prebuild workflow. Without this, the committed app source is not wired into root Premake config. |
| `repo.toml` | must-track in first commit | Include if the first commit includes `source/apps/my_own_software.kit` | Adds the app to `[repo_precache_exts].apps`, making extension precache target the product app. This is part of the Kit workflow integration. |

## 4. Documentation Files

| Path | Classification | First commit recommendation | Rationale |
| --- | --- | --- | --- |
| `docs/architecture/current_repository_analysis_codex.md` | should-track in first commit | Include | Architecture source-of-truth generated in Ticket 001. |
| `docs/architecture/generated_runtime_artifacts_policy.md` | should-track in first commit | Include | Repository hygiene policy generated in Ticket 002. |
| `docs/architecture/first_commit_source_classification.md` | should-track in first commit | Include | This first-commit planning document. |
| `docs/07_USD_MODELING_CONVENTIONS.md` | should-track in first commit | Include | Project-specific USD/AEC modeling convention document. It appears intentional and belongs in docs. |
| `current_repository_analysis.md` | optional / owner decision | Do not include by default | The task history explicitly says it is not source of truth. It may be useful as an archived prior interpretation, but should not be committed unless the owner wants it retained. |

## 5. Root Context Files

| Path | Classification | First commit recommendation | Rationale |
| --- | --- | --- | --- |
| `00_PROJECT_CONTEXT.txt` | optional / owner decision | Include only if owner wants root-level operating notes committed as-is | Appears project-specific and small, but root-level `.txt` organization should be decided. |
| `01_RULES_AND_LIMITATIONS.txt` | optional / owner decision | Include only if owner wants root-level operating notes committed as-is | Project guidance; may belong under `docs/` later. |
| `02_TASKS_BACKLOG.txt` | optional / owner decision | Include only if owner wants backlog snapshot committed | Could become stale quickly; consider moving later to docs/issues. |
| `03_USD_CONVENTIONS.txt` | optional / owner decision | Include only if owner wants it alongside docs | May duplicate or predate `docs/07_USD_MODELING_CONVENTIONS.md`. |
| `04_CODEX_WORKFLOW.txt` | optional / owner decision | Include only if owner wants Codex workflow notes versioned | Useful process note, but location needs decision. |
| `05_MIGRATION_MAP.txt` | optional / owner decision | Include only if owner wants migration snapshot versioned | Could be valuable, but should probably move into `docs/architecture/` later. |
| `06_EXTENSION_PLAYBOOK.txt` | optional / owner decision | Include only if owner wants extension workflow notes committed | Likely useful; location/format should be reviewed. |
| `07_PROFESIONAL_VISUALIZATION.txt` | optional / owner decision | Include only if owner approves root-level design/visualization notes | Large and project-specific; typo in filename may be worth fixing in a future move/rename ticket, not this one. |
| `digital_twin_contexto_maestro.md` | optional / owner decision | Do not include by default without owner review | Large context document. Likely valuable, but may contain broad/strategic context not appropriate for first code commit without review. |

Recommendation: do not stage root context files in the first technical source commit unless the owner explicitly wants them included as-is. A later documentation organization ticket can move/normalize them under `docs/`.

## 6. Source Apps

| Path | Classification | First commit recommendation | Rationale |
| --- | --- | --- | --- |
| `source/apps/my_own_software.kit` | must-track in first commit | Include | Active product Kit app descriptor. Required to launch/build the app composition. |
| `source/apps/my_own_software.kit.before_extension_cleanup` | optional / owner decision | Do not include by default | Backup/snapshot file. Useful migration history only if owner wants it. Not required for runtime. |

## 7. Source Extensions

All active local extension folders should be included in the first project source commit, except ignored pycache/bytecode and any later owner-excluded backup/generated files.

| Extension folder | Classification | First commit recommendation | Rationale |
| --- | --- | --- | --- |
| `source/extensions/custom.aec.sketch` | must-track in first commit | Include folder | Active AEC sketch extension loaded by the app. Includes data icons/preview, docs, tests, config, Premake, Python source. |
| `source/extensions/custom.aec.primitive_mesh` | must-track in first commit | Include folder | Active primitive mesh extension used directly and by modeling. |
| `source/extensions/custom.aec.extrude` | must-track in first commit | Include folder | Active extrusion extension used by modeling. |
| `source/extensions/custom.aec.modeling` | must-track in first commit | Include folder | Central AEC modeling extension and API. |
| `source/extensions/custom.aec.thermal_viz` | must-track in first commit | Include folder | Active thermal visualization/telemetry extension. Include sample CSV because it is extension sample data referenced by the feature. |
| `source/extensions/dt.energy.agent` | must-track in first commit | Include folder | Active Energy Twin Agent extension, including tool registry, IDF placeholder, disabled EnergyPlus runner, UI, and LLM stubs. |
| `source/extensions/my_company.my_usd_composer_setup_extension` | must-track in first commit | Include folder | Active app setup extension required by `my_own_software.kit`, including layout, stage template, app defaults, and bundled materials/icons. |

### Files Inside Extensions to Include

Include:

- `config/extension.toml`
- `premake5.lua`
- Python package source
- extension-local `.gitignore` files
- source docs/README files
- sample data needed for extension behavior or demos, such as `custom.aec.thermal_viz/data/sample_temperature_day.csv`
- UI assets, icons, previews, layouts, USD/USDA/MDL material assets that are part of the extension runtime
- current template-generated tests, but mark them for review after first commit

### Files Inside Extensions to Exclude

Exclude:

- `source/**/__pycache__/`
- `source/**/*.pyc`
- any generated runtime output copied from `_build`

Validation observed:

- `__pycache__` directories exist under source extensions.
- `.pyc` files exist under source extensions.
- Root `.gitignore` and extension-local `.gitignore` files ignore those cache files.

### Template-Generated Tests

Recommendation: include tests in first commit if they are inside active extension folders, because they document the generated Kit extension baseline and may be used by `repo` test scripts. Open a later test-quality ticket to separate real tests from template placeholders.

## 8. Source Metadata

| Path | Classification | First commit recommendation | Rationale |
| --- | --- | --- | --- |
| `source/rendered_template_metadata.json` | optional / owner decision | Include only if owner wants to preserve Kit template render provenance | It is auto-generated and includes stale-looking metadata such as `try.one`, but it may document how the app/extensions were rendered from templates. Not required for runtime based on current inspection. |
| `source/source_tree.txt` | should-ignore | Do not stage | Generated analysis/tree dump; ignored by `.gitignore`. |

## 9. Vendor / Archive / Generated Dumps

| Path | Classification | First commit recommendation | Rationale |
| --- | --- | --- | --- |
| `CustomPrimitiveMesh.zip` | optional / owner decision / vendor/archive | Do not include by default | Archive artifact of unclear ownership/purpose. Commit only with explicit owner approval and preferably after documenting why it belongs in Git. |
| `repo_tree.txt` | should-ignore | Do not stage | Generated dump; ignored. |
| `source_tree.txt` | should-ignore | Do not stage | Generated dump; ignored. |
| `tools_tree.txt` | should-ignore | Do not stage | Generated dump; ignored. |
| `important_files.txt` | should-ignore | Do not stage | Large generated dump; ignored. |
| `extensions_list.txt` | should-ignore | Do not stage | Generated extension list; ignored. |
| `templates/templates_tree.txt` | should-ignore | Do not stage | Generated dump inside tracked template tree; ignored. |

## 10. Recommended First Commit Contents

Recommended default first commit:

- `.gitignore`
- `premake5.lua`
- `repo.toml`
- architecture/docs generated by Tickets 001-004
- `docs/07_USD_MODELING_CONVENTIONS.md`
- active app descriptor `source/apps/my_own_software.kit`
- all active local extension folders under `source/extensions`

Do not include by default:

- root context `.txt` files
- `digital_twin_contexto_maestro.md`
- `current_repository_analysis.md`
- `source/rendered_template_metadata.json`
- `source/apps/my_own_software.kit.before_extension_cleanup`
- `CustomPrimitiveMesh.zip`
- generated dumps and cache files

## 11. Proposed Staging Commands

Do not run these commands in this ticket. They are the proposed explicit staging plan for a later commit-preparation ticket.

```powershell
git add .gitignore
git add premake5.lua
git add repo.toml

git add docs/07_USD_MODELING_CONVENTIONS.md
git add docs/architecture/current_repository_analysis_codex.md
git add docs/architecture/generated_runtime_artifacts_policy.md
git add docs/architecture/first_commit_source_classification.md

git add source/apps/my_own_software.kit

git add source/extensions/custom.aec.sketch
git add source/extensions/custom.aec.primitive_mesh
git add source/extensions/custom.aec.extrude
git add source/extensions/custom.aec.modeling
git add source/extensions/custom.aec.thermal_viz
git add source/extensions/dt.energy.agent
git add source/extensions/my_company.my_usd_composer_setup_extension
```

Optional owner-approved additions only:

```powershell
git add 00_PROJECT_CONTEXT.txt
git add 01_RULES_AND_LIMITATIONS.txt
git add 02_TASKS_BACKLOG.txt
git add 03_USD_CONVENTIONS.txt
git add 04_CODEX_WORKFLOW.txt
git add 05_MIGRATION_MAP.txt
git add 06_EXTENSION_PLAYBOOK.txt
git add 07_PROFESIONAL_VISUALIZATION.txt
git add digital_twin_contexto_maestro.md
git add source/rendered_template_metadata.json
git add source/apps/my_own_software.kit.before_extension_cleanup
```

Do not use `git add .` for the first real project commit.

## 12. Explicit Do-Not-Stage Paths

Do not stage these by default:

```text
CustomPrimitiveMesh.zip
current_repository_analysis.md
repo_tree.txt
source_tree.txt
tools_tree.txt
important_files.txt
extensions_list.txt
source/source_tree.txt
templates/templates_tree.txt
source/**/__pycache__/
source/**/*.pyc
_build/
_compiler/
_repo/
```

Do not stage these without explicit owner approval:

```text
00_PROJECT_CONTEXT.txt
01_RULES_AND_LIMITATIONS.txt
02_TASKS_BACKLOG.txt
03_USD_CONVENTIONS.txt
04_CODEX_WORKFLOW.txt
05_MIGRATION_MAP.txt
06_EXTENSION_PLAYBOOK.txt
07_PROFESIONAL_VISUALIZATION.txt
digital_twin_contexto_maestro.md
source/rendered_template_metadata.json
source/apps/my_own_software.kit.before_extension_cleanup
```

## 13. Validation Commands Before First Commit

Run before staging:

```powershell
git status --short
git diff -- .gitignore
git diff -- premake5.lua
git diff -- repo.toml
git check-ignore -v repo_tree.txt
git check-ignore -v source_tree.txt
git check-ignore -v tools_tree.txt
git check-ignore -v important_files.txt
git check-ignore -v extensions_list.txt
git check-ignore -v source/source_tree.txt
git check-ignore -v templates/templates_tree.txt
git check-ignore -v source/apps/my_own_software.kit
git check-ignore -v source/extensions/custom.aec.modeling/config/extension.toml
git check-ignore -v source/extensions/dt.energy.agent/config/extension.toml
git check-ignore -v source/extensions/dt.energy.agent/dt/__pycache__/__init__.cpython-312.pyc
git ls-files source
```

Expected:

- Product source paths return no ignore rule.
- Generated dumps and pycache return ignore rules.
- `git ls-files source` remains empty before staging and lists source files after staging.

Run after proposed staging, before commit:

```powershell
git diff --cached --stat
git diff --cached --name-only
git status --short
git check-ignore -v source/apps/my_own_software.kit
git check-ignore -v source/extensions/custom.aec.modeling/config/extension.toml
git check-ignore -v source/extensions/dt.energy.agent/dt/__pycache__/__init__.cpython-312.pyc
```

Do not run build or launch as part of this review ticket. A later validation ticket should run the Kit workflow.

## 14. Risks

- The first source commit will be large because all product source under `source/` is currently untracked.
- `premake5.lua` and `repo.toml` are required for Kit workflow integration, but they were modified before this ticket; review their changes before staging.
- Including `my_company.my_usd_composer_setup_extension` preserves active app behavior but also commits template-derived setup code and assets.
- Template-generated tests may be weak or stale; include them for baseline continuity, then review later.
- Excluding root context files from the first commit may omit useful project context; including them may clutter root and commit stale planning notes. Owner decision required.
- `source/rendered_template_metadata.json` may be useful provenance or stale generated metadata. Owner decision required.
- `CustomPrimitiveMesh.zip` should not enter Git without explicit vendor/archive policy.

## 15. Recommended Next Ticket

Recommended next ticket: perform owner-reviewed staging only.

Suggested scope:

- Apply the explicit `git add` commands from this document.
- Do not use `git add .`.
- Run `git diff --cached --stat` and `git diff --cached --name-only`.
- Confirm no pycache, generated dumps, `_build`, `_repo`, `_compiler`, or zip/vendor artifacts are staged.
- Stop before commit for final review, or commit only if explicitly authorized.
