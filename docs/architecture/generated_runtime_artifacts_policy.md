# Generated and Runtime Artifacts Policy

Date: 2026-05-24

Scope: documentation-only classification for repository hygiene. No files were deleted, moved, or cleaned as part of this ticket.

Context source: `docs/architecture/current_repository_analysis_codex.md` was used as background, and relevant paths were independently rechecked against the current filesystem, `git status`, `git ls-files`, `.gitignore`, and sample `git check-ignore` results.

## 1. Executive Summary

This repository is an NVIDIA Omniverse Kit App Template derivative. It contains a mix of authored project source, Kit-managed template/tooling source, generated build outputs, runtime app state, extension caches, logs, local developer state, and temporary analysis dumps.

The most important policy finding is that the active product source currently lives under `source/`, but the current `.gitignore` contains `/source`, causing `source/apps`, `source/extensions`, `source/rendered_template_metadata.json`, and `source/source_tree.txt` to be ignored as a group. That may have been inherited from the template workflow, but it conflicts with treating local app and extension code as source-of-truth. This document recommends changing that policy in a future ticket, not in this one.

The second important finding is that `_build/`, `_compiler/`, and `_repo/` are correctly ignored by the broad `_*/` rule, but they must not be treated casually. They are generated/Kit-managed local workflow state used for build, launch, dependency resolution, extension cache, and runtime logs. They can usually be regenerated, but cleanup should be coordinated with Kit workflow validation.

EnergyPlusV24-2-0 was requested for special attention. It was not present at the repository root during inspection. If added later, it should be classified as `vendor/external` pending an explicit dependency and redistribution decision.

## 2. Classification Categories

| Category | Should be committed? | May Codex edit? | May be deleted safely? | Should be gitignored? | Special cleanup procedure |
| --- | --- | --- | --- | --- | --- |
| source-of-truth | Yes | Yes, when task explicitly modifies project source | No | No | Review, test, and commit normally |
| Kit-managed source | Usually yes if inherited template source is part of repo | Only with care and explicit task scope | No | No | Check Kit template assumptions before changes |
| Kit-managed tooling | Yes for bootstrapping scripts/manifests; no for downloaded tool caches | Rarely | No for tracked bootstrap files; yes for generated caches | Mixed | Validate `repo.bat` / `repo.sh` workflow after changes |
| generated build artifact | No | No, except generated inspection only | Yes, after confirming it is not the only copy of source | Yes | Regenerate through Kit build/prebuild tooling |
| runtime artifact | No | No | Usually yes, after app is closed | Yes | Close Kit app first; preserve logs only if debugging |
| cache | No | No | Usually yes | Yes | Expect network/re-fetch cost after deletion |
| logs | No | No | Yes unless needed for debugging | Yes | Archive only when diagnosing a specific run |
| temporary analysis dump | Usually no | Yes only for docs/inventory tasks | Yes after review | Yes | Confirm no unique source content inside |
| vendor/external | Decision needed | No unless task is vendor integration | Not without owner approval | Usually yes or Git LFS/artifact manager | Verify license, size, reproducibility, and required path |
| template/scaffolding | Yes if repo still ships template library | Yes only when modifying template system | No | No, except generated template dumps | Validate template rendering if changed |
| local developer configuration | Mixed | Usually no | Usually yes for user-specific files | Usually yes for user-specific files | Preserve shared launch/tasks if intentionally tracked |
| unknown / needs decision | No until classified | No | No | Maybe | Assign owner and source-of-truth decision first |

## 3. Path Classification

### Source-of-Truth

| Path | Category | Commit? | Codex edit? | Delete safely? | Gitignore? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `docs/` | source-of-truth | Yes | Yes for documentation tasks | No | No | Project architecture and conventions docs. Currently untracked as a folder in `git status`, but should be committed if documentation is intended to persist. |
| `docs/architecture/current_repository_analysis_codex.md` | source-of-truth | Yes | Yes for follow-up docs | No | No | Prior architecture analysis. |
| `docs/architecture/generated_runtime_artifacts_policy.md` | source-of-truth | Yes | Yes | No | No | This policy document. |
| `source/apps/my_own_software.kit` | source-of-truth | Yes, if this product app is intended to be versioned | Yes only for app composition tasks | No | No | Active app descriptor. Currently ignored by `/source`; future `.gitignore` policy should unignore source. Contains generated Kit version-lock block, so manual edits require care. |
| `source/extensions/` | source-of-truth | Yes, if local extensions are product source | Yes for implementation tasks | No | No | Local AEC, thermal, energy agent, and setup extensions. Currently ignored by `/source`; this is a major policy mismatch. |
| Root project guidance files `00_PROJECT_CONTEXT.txt` through `07_PROFESIONAL_VISUALIZATION.txt` | source-of-truth / unknown | Decision needed | Yes for docs tasks | No until classified | No if retained | Appear project-specific and currently untracked. Should be either committed as docs or moved into docs in a future migration ticket. |
| `digital_twin_contexto_maestro.md` | source-of-truth / unknown | Decision needed | Yes for docs tasks | No until classified | No if retained | Large project context document, currently untracked. |
| `current_repository_analysis.md` | unknown / needs decision | Decision needed | Prefer no | No until superseded | Maybe | Prior analysis, explicitly not source of truth for Ticket 001. Decide whether to archive, replace, or ignore. |

### Kit-Managed Source

| Path | Category | Commit? | Codex edit? | Delete safely? | Gitignore? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `repo.toml` | Kit-managed source | Yes | Only when task explicitly changes repo tooling | No | No | Imports Kit template repo configs and defines build/package/precache behavior. Currently modified before this ticket. |
| `premake5.lua` | Kit-managed source | Yes | Only when task explicitly changes build/app definition | No | No | Defines Kit setup and `my_own_software.kit`. Currently modified before this ticket. |
| `repo.bat`, `repo.sh`, `repo_tools.toml` | Kit-managed source/tooling | Yes | Rarely | No | No | Bootstrap and command behavior. |
| `.editorconfig`, `.gitattributes`, `.gitignore` | Kit-managed/project source | Yes | `.gitignore` only in a future policy update ticket | No | No | Current `.gitignore` has important inherited assumptions. |
| `LICENSE`, `PRODUCT_TERMS_OMNIVERSE`, `SECURITY.md`, `CHANGELOG.md`, `README.md` | Kit-managed source / project metadata | Yes | Usually no unless docs/legal task | No | No | Upstream template/project metadata. |
| `.github/` | Kit-managed source / CI scaffolding | Yes | Yes only for CI/template tasks | No | No | Tracked upstream workflow and replay files. |
| `readme-assets/` | Kit-managed source / docs assets | Yes while README/template docs use them | Yes only for docs tasks | No | No | Tracked README imagery and supplemental docs. |

### Kit-Managed Tooling

| Path | Category | Commit? | Codex edit? | Delete safely? | Gitignore? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `tools/` | Kit-managed tooling | Yes for current checked-in bootstrap files | No except explicit tooling tasks | No for tracked files | No, except generated caches under it | Contains Packman, Repoman, dependency manifests, package scripts. Tracked by `git ls-files`. |
| `tools/deps/*.packman.xml`, `tools/deps/pip.toml`, `tools/deps/user.toml` | Kit-managed tooling | Yes | Rarely | No | No, except user-specific Packman `.user` files | Dependency manifests used by repo tooling. |
| `tools/repoman/__pycache__/` | cache | No | No | Yes | Yes | Python bytecode cache inside tooling; should be ignored/cleaned if present. |
| `_repo/deps/` | Kit-managed tooling cache | No | No | Usually yes, but can break local workflow until re-fetched | Yes | Downloaded/linked repo-tool dependencies. Required for local commands after bootstrap, but not source-of-truth. |
| `_repo/repo.log` | logs | No | No | Yes | Yes | Repo command log. Ignored by `_*/`. |

### Generated Build Artifacts

| Path | Category | Commit? | Codex edit? | Delete safely? | Gitignore? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `_build/` | generated build artifact / runtime root | No | No | Usually yes after closing apps, but may require rebuild/fetch | Yes | Broadly ignored by `_*/`. Contains generated apps, copied exts, dependency links, runtime, caches, logs. Do not edit as source. |
| `_build/apps/exts.deps.generated.kit` | generated build artifact | No | No | Yes, regenerated | Yes | Generated extension dependency Kit file. |
| `_build/generated/prebuild.toml` | generated build artifact | No | No | Yes, regenerated | Yes | Prebuild state. |
| `_build/deps/user.toml` | generated copy | No | No | Yes, regenerated from `tools/deps/user.toml` | Yes | Copied by root `premake5.lua`. |
| `_build/host-deps/` | generated/tool dependency | No | No | Yes with re-fetch cost | Yes | Host Premake/Python links/deps. |
| `_build/target-deps/` | generated/tool dependency | No | No | Yes with re-fetch cost | Yes | Target Python/SDK/build dependencies. |
| `_build/windows-x86_64/debug/` | generated build artifact | No | No | Yes, regenerated | Yes | Generated launch/test batch files and dev metadata. |
| `_build/windows-x86_64/release/exts/` | generated build artifact | No | No | Yes, regenerated from `source/extensions` | Yes | Runtime copies/links of local extensions. Never treat as source. |
| `_build/windows-x86_64/release/extsbuild/` | generated build artifact/cache | No | No | Yes, regenerated/fetched | Yes | Built/cached external extension dependencies. |
| `_build/windows-x86_64/release/compile_commands.json` | generated build artifact | No | No | Yes | Yes | Generated compile database. |
| `_build/windows-x86_64/*/tests-*.bat`, `kit.bat`, `my_own_software.kit.bat` | generated launch/test artifacts | No | No | Yes, regenerated | Yes | Generated by Kit repo tooling. |

### Runtime Artifacts, Caches, and Logs

| Path | Category | Commit? | Codex edit? | Delete safely? | Gitignore? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `_build/windows-x86_64/release/kit/` | vendor/runtime artifact | No | No | Usually yes with re-fetch/reinstall cost | Yes | Kit SDK runtime link/content. Required to launch locally after fetch. |
| `_build/windows-x86_64/release/extscache/` | cache/vendor runtime | No | No | Yes with re-fetch cost | Yes | Cached external Omniverse extensions from registries. |
| `_build/windows-x86_64/release/cache/` | runtime cache | No | No | Yes if app closed | Yes | Kit runtime cache. |
| `_build/windows-x86_64/release/data/` | runtime data | No | No | Usually yes if app closed | Yes | Runtime app data. Check before deleting if debugging app state. |
| `_build/windows-x86_64/release/logs/` | logs | No | No | Yes unless preserving diagnostics | Yes | Kit launch logs. |
| `_build/windows-x86_64/release/site/sitecustomize.py` | generated runtime artifact | No | No | Yes, regenerated | Yes | Generated runtime Python site customization. |
| `_build/PACKAGE-LICENSES/`, `_build/windows-x86_64/release/PACKAGE-LICENSES/` | generated package/license artifact | No | No | Yes, regenerated | Yes | Generated license outputs for packaged dependencies. |
| `_compiler/` | generated/toolchain pointer/cache | No | No | Yes with caution; may be symlink/junction-like | Yes | Contains `current`, which produced path read errors during recursive inspection. Cleanup should be handled with a deliberate Windows-safe procedure. |

### Python Bytecode

| Path | Category | Commit? | Codex edit? | Delete safely? | Gitignore? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `source/**/__pycache__/` | cache | No | No | Yes | Yes | Found under all major local extension packages. Should be removed in cleanup Phase 2. |
| `source/**/*.pyc` | cache | No | No | Yes | Yes | Ignored currently because `/source` ignores everything and `*.py[cod]` also applies. |
| `tools/**/__pycache__/`, `_build/**/*.pyc`, `_repo/**/*.pyc` | cache | No | No | Yes, with generated/runtime caveats | Yes | Tool/runtime bytecode. No source value. |
| `*.pyc`, `*.pyo`, `*.pyd` | cache / binary extension outputs | Usually no | No | Usually yes | Yes | Current `.gitignore` has `*.py[cod]`; future policy should also include `__pycache__/`. |

### Temporary Analysis Dumps

| Path | Category | Commit? | Codex edit? | Delete safely? | Gitignore? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `repo_tree.txt` | temporary analysis dump | No, unless intentionally archived | Yes for analysis tasks | Yes after review | Yes | Large generated tree dump. Currently untracked. |
| `source_tree.txt` | temporary analysis dump | No, unless intentionally archived | Yes for analysis tasks | Yes after review | Yes | Generated tree dump. Currently untracked. |
| `tools_tree.txt` | temporary analysis dump | No, unless intentionally archived | Yes for analysis tasks | Yes after review | Yes | Generated tree dump. Currently untracked. |
| `important_files.txt` | temporary analysis dump | No, unless intentionally archived | Yes for analysis tasks | Yes after review | Yes | Large generated file inventory/dump. Currently untracked. |
| `extensions_list.txt` | temporary analysis dump | No, unless intentionally archived | Yes for analysis tasks | Yes after review | Yes | Generated extension list. Currently untracked. |
| `source/source_tree.txt` | temporary analysis dump inside source | No | Yes for analysis tasks | Yes after review | Yes | Should not live in source-of-truth tree. |
| `templates/templates_tree.txt` | temporary analysis dump inside template tree | No | Yes for analysis tasks | Yes after review | Yes | Should not live inside tracked template/scaffolding area unless intentionally documented. |

### Vendor / External

| Path | Category | Commit? | Codex edit? | Delete safely? | Gitignore? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `CustomPrimitiveMesh.zip` | vendor/external / archive artifact | Decision needed | No | No until owner decides | Maybe | Untracked zip at repo root. Could be a source archive, vendor dependency, or historical artifact. Needs owner decision before cleanup. |
| `EnergyPlusV24-2-0/` | vendor/external | Decision needed if present | No | No without owner approval | Usually yes or artifact-managed | Not present during inspection. If introduced, classify as external runtime/vendor dependency pending license, size, path, and reproducibility decision. |
| `_build/windows-x86_64/release/kit/` | vendor/runtime artifact | No | No | Yes with re-fetch cost | Yes | Local Kit runtime. |
| `_build/windows-x86_64/release/extscache/` | vendor/runtime cache | No | No | Yes with re-fetch cost | Yes | External extension cache from Kit registries. |
| `templates/**/data/*.mdl`, `*.usda`, images | template/scaffolding with vendor-like assets | Yes if template library retained | No except template tasks | No | No | Tracked template assets from Kit template. Treat as template source, not generated runtime. |

### Template / Scaffolding

| Path | Category | Commit? | Codex edit? | Delete safely? | Gitignore? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `templates/` | template/scaffolding | Yes while repo retains Kit template capability | Yes only for template tasks | No | No | Tracked by `git ls-files`; includes app/extension templates. |
| `templates/templates.toml` | template/scaffolding | Yes | Yes only for template tasks | No | No | Template registry. |
| `templates/apps/**` | template/scaffolding | Yes | Yes only for template tasks | No | No | Kit sample app templates. |
| `templates/extensions/**` | template/scaffolding | Yes | Yes only for template tasks | No | No | Kit extension templates. |
| `.github/workflows/replay_files/**`, `.vscode/replay_files/**` | template/scaffolding / local dev support | Yes if template replay tooling is retained | Rarely | No | No | Tracked template replay inputs. |

### Local Developer Configuration

| Path | Category | Commit? | Codex edit? | Delete safely? | Gitignore? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `.vscode/launch.json`, `.vscode/tasks.json`, `.vscode/template_builder.py`, `.vscode/replay_files/**` | local developer configuration / template scaffolding | Currently tracked; commit if shared workflow is intentional | Rarely | No if tracked shared tooling | No for shared files | This repo tracks shared VS Code config. User-specific `.vscode/settings.json` is ignored. |
| `.vscode/settings.json` | local developer configuration | No | No | Yes | Yes | Already ignored. |
| `.omniverse_eula_accepted.txt` | local developer/runtime marker | No | No | Yes if local only | Yes | Already ignored by `.gitignore`; currently exists locally. |
| `.vs/`, `.idea/`, `.DS_Store`, `.cache`, `.local`, `.nvidia-omniverse` | local developer configuration/cache | No | No | Yes | Yes | Already covered by current `.gitignore` for several cases. |

### Unknown / Needs Decision

| Path | Category | Commit? | Codex edit? | Delete safely? | Gitignore? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `source/rendered_template_metadata.json` | unknown / generated template metadata | Decision needed | No unless template task | No until classified | Maybe | File says auto-generated. It records rendered templates and stale-looking `try.one` metadata. Decide whether Kit tooling still requires it. |
| `source/apps/my_own_software.kit.before_extension_cleanup` | unknown / temporary backup | Usually no | No | Not until owner confirms active app has superseded it | Yes if retained temporarily | Snapshot/backup beside active app descriptor. Should not remain long-term source unless explicitly archived. |
| `current_repository_analysis.md` | unknown / prior analysis | Decision needed | No | Not until docs are reconciled | Maybe | Replaced as source of truth by Codex analysis for Ticket 001, but may contain useful context. |
| Root `*_tree.txt`, `important_files.txt`, `extensions_list.txt` | temporary analysis dump | No | Yes for analysis | Yes after review | Yes | Currently untracked and not ignored by current `.gitignore` unless matching another rule. |

## 4. Current Git Tracking and Ignore Observations

Observed with read-only commands:

- `git status --short` shows pre-existing modifications to `premake5.lua` and `repo.toml`.
- `docs/` is currently untracked as a folder.
- Root project docs and generated dumps are currently untracked.
- `CustomPrimitiveMesh.zip` is currently untracked.
- `templates/templates_tree.txt` is currently untracked even though most of `templates/` is tracked.
- `source/` does not appear in `git status` because the current `.gitignore` ignores `/source`.
- `git check-ignore -v` confirmed:
  - `_build/apps/exts.deps.generated.kit` ignored by `_*/`
  - `_repo/repo.log` ignored by `_*/`
  - `source/extensions/.../__pycache__/...pyc` ignored by `/source`
  - `source/source_tree.txt` ignored by `/source`
- `git ls-files` confirmed tracked template/tooling areas:
  - `.vscode/*` shared files
  - `templates/**`
  - `tools/**`
  - root Kit metadata and bootstrap files

Policy issue: `/source` is too broad if this repository is now a product repo whose active app and extensions live under `source/`.

## 5. Future `.gitignore` Policy Proposal

Do not edit `.gitignore` in this ticket. In a future ticket, consider changing it from broad template ignores to product-source-aware ignores.

### Recommended Additions / Adjustments

```gitignore
# Kit / repo generated outputs
_build/
_compiler/
_repo/

# Python bytecode
__pycache__/
*.py[cod]
*$py.class

# Generated tree / analysis dumps
repo_tree.txt
source_tree.txt
tools_tree.txt
important_files.txt
extensions_list.txt
source/source_tree.txt
templates/templates_tree.txt

# Local runtime / user state
.omniverse_eula_accepted.txt
.vs/
.idea/
.DS_Store
.cache/
.local/
.nvidia-omniverse/
.vscode/settings.json

# Kit/package generated files
PACKAGE-DEPS.yaml
*.packman.xml.user

# Optional vendor/runtime bundles pending explicit artifact policy
EnergyPlusV24-2-0/
```

### Recommended Change Requiring Review

Current rule:

```gitignore
/source
```

Recommended future direction:

```gitignore
# Do not ignore product source.
# /source should be tracked selectively once source ownership is confirmed.
```

If the team still needs to ignore generated source from template rendering, replace `/source` with precise generated-file patterns rather than ignoring the entire product source tree.

### Optional Vendor Policy Entries

Only after owner decision:

```gitignore
CustomPrimitiveMesh.zip
*.zip
```

Do not add broad `*.zip` if release archives, fixtures, or required sample packages are intentionally committed.

## 6. Phased Cleanup Plan

### Phase 0 - No-Op / Documentation Only

Status: this ticket.

Actions:

- Document classifications.
- Document current tracking/ignore mismatches.
- Do not delete, move, or edit code/config.
- Do not edit `.gitignore`.

Validation:

- `git status --short`
- `git ls-files`
- selective `git check-ignore -v`

### Phase 1 - Remove Obvious Generated Files from Source Tree

Candidate removals, after owner approval:

- `source/source_tree.txt`
- `templates/templates_tree.txt`
- root `repo_tree.txt`
- root `source_tree.txt`
- root `tools_tree.txt`
- root `important_files.txt`
- root `extensions_list.txt`

Rules:

- Review contents first.
- Confirm they are generated inventories with no unique source content.
- Remove using a dedicated cleanup commit.
- Do not touch `_build`, `_repo`, `_compiler` in this phase.

### Phase 2 - Clean Local Caches and Pycache

Candidate removals:

- `source/**/__pycache__/`
- `source/**/*.pyc`
- `tools/**/__pycache__/`

Optional local-only cleanup after app is closed:

- `_build/**/__pycache__/`
- `_build/windows-x86_64/release/logs/`
- `_repo/repo.log`

Rules:

- Use Windows-safe deletion commands only after reviewing absolute paths.
- Do not remove source files.
- Do not clean `_compiler/current` casually because it appears symlink/junction-like and produced read errors during traversal.

### Phase 3 - `.gitignore` Policy Update

Candidate policy changes:

- Replace broad `/source` ignore with source-aware rules.
- Add explicit generated dump patterns.
- Add `__pycache__/`.
- Preserve `_*/` or replace with explicit `_build/`, `_compiler/`, `_repo/` if broader underscore directories might become source later.
- Add `EnergyPlusV24-2-0/` only if the vendor policy says local install should not be committed.

Required review:

- Verify whether `source/apps` and `source/extensions` should be committed.
- Verify whether any generated source folders are expected by Kit template render workflows.
- Confirm tracked `.vscode` files remain intentionally shared.

### Phase 4 - Decide Vendor / Runtime Relocation

Decision items:

- `CustomPrimitiveMesh.zip`: keep, move to artifact store, unpack/reference, or ignore?
- `EnergyPlusV24-2-0/`: if introduced, should it live outside repo, in a documented local path, in package manager config, in Git LFS, or in an artifact store?
- `_build/windows-x86_64/release/kit` and `extscache`: should remain local generated/runtime cache, not committed.

Rules:

- Do not delete vendor/external artifacts until ownership, license, and reproducibility are clear.
- Avoid committing large vendor runtimes directly to Git unless explicitly approved.

### Phase 5 - Validate Build / Launch After Cleanup

After cleanup and `.gitignore` update, validate the Kit workflow.

Suggested commands:

```powershell
git status --short
git check-ignore -v source/apps/my_own_software.kit
git check-ignore -v source/extensions/dt.energy.agent/config/extension.toml
git check-ignore -v _build/apps/exts.deps.generated.kit
git check-ignore -v source/extensions/dt.energy.agent/dt/__pycache__/__init__.cpython-312.pyc
.\repo.bat build
.\repo.bat launch --app my_own_software
```

Build/launch commands are intentionally not run in this ticket.

## 7. Risks

- Ignoring `/source` can hide product code changes from Git. This is the highest repository hygiene risk found.
- Editing `_build/windows-x86_64/release/exts` would modify generated runtime copies, not source-of-truth.
- Deleting `_build` is usually recoverable, but it may force large Kit SDK and extension re-fetches and can disrupt local launch until regenerated.
- Deleting `_repo/deps` can break `repo.bat` commands until dependencies are re-fetched.
- `_compiler/current` may be a symlink/junction-like path. Treat cleanup as a special Windows-safe operation.
- Removing `source/rendered_template_metadata.json` may affect template tooling if it still expects metadata.
- Removing `source/apps/*.before_extension_cleanup` may discard useful migration history if not archived elsewhere.
- Vendor/runtime artifacts such as `CustomPrimitiveMesh.zip` and future `EnergyPlusV24-2-0/` require license, size, source, and reproducibility decisions.
- Broad `*.zip` ignore rules may accidentally hide intentional fixtures or release artifacts.

## 8. Read-Only Validation Commands Used

Commands used for this classification:

```powershell
Get-ChildItem -Force
Get-Content docs\architecture\current_repository_analysis_codex.md | Select-Object -First 80
git status --short
git ls-files
Get-ChildItem -Force source,docs,templates,tools,_build,_compiler,_repo | Select-Object FullName,Mode,Length,LastWriteTime
Test-Path EnergyPlusV24-2-0
Get-ChildItem -Force -Directory | Where-Object { $_.Name -like '*Energy*' } | Select-Object FullName,Name,LastWriteTime
Get-ChildItem -Recurse -Force source -Directory | Where-Object { $_.Name -eq '__pycache__' } | Select-Object FullName
Get-ChildItem -Recurse -Force source -File -Include *.pyc | Select-Object FullName,Length | Select-Object -First 80
Get-ChildItem -Recurse -Force . -File -Include repo_tree.txt,source_tree.txt,tools_tree.txt,important_files.txt,extensions_list.txt,templates_tree.txt | Select-Object FullName,Length
Get-Content .gitignore
git check-ignore -v _build\apps\exts.deps.generated.kit _repo\repo.log source\extensions\dt.energy.agent\dt\__pycache__\__init__.cpython-312.pyc repo_tree.txt source\source_tree.txt templates\templates_tree.txt CustomPrimitiveMesh.zip docs\architecture\current_repository_analysis_codex.md
git ls-files _build _repo _compiler source docs templates tools .vscode CustomPrimitiveMesh.zip repo_tree.txt source_tree.txt tools_tree.txt important_files.txt extensions_list.txt
Get-ChildItem -Recurse -Depth 2 -Force _build\windows-x86_64\release | Select-Object FullName,Mode,Length | Select-Object -First 120
Get-ChildItem -Recurse -Depth 2 -Force _build\windows-x86_64\debug | Select-Object FullName,Mode,Length | Select-Object -First 80
```

One recursive listing over `.` reported a read error under `_compiler/current`, reinforcing the need for a special cleanup procedure for `_compiler`.

## 9. Recommended Next Ticket

Recommended next ticket: update repository ignore policy without deleting files.

Suggested scope:

- Decide whether `source/apps` and `source/extensions` are now product source-of-truth.
- Replace or refine the broad `/source` ignore rule.
- Add explicit ignore entries for generated analysis dumps and `__pycache__/`.
- Add an explicit vendor policy placeholder for `EnergyPlusV24-2-0/`.
- Validate with `git check-ignore -v` for representative source, generated, cache, and vendor paths.

Do not combine `.gitignore` changes with cleanup deletion in the same ticket. Keep policy changes and physical cleanup separate for reviewability.
