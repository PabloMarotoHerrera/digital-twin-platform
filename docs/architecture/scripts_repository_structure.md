# Scripts Repository Structure Contract

Status: proposed architecture contract  
Scope: future root `scripts/` structure only  
Date: 2026-05-24

## 1. Executive Summary

This repository does not currently have a root-level `scripts/` directory. Existing executable
tooling is primarily inherited from the NVIDIA Omniverse Kit App Template:

- `repo.bat` and `repo.sh` are the official repo entrypoints.
- `tools/` contains Kit/Packman/Repoman tooling.
- `templates/` contains scaffold templates.
- `premake5.lua` and extension-local `premake5.lua` files define Kit build integration.
- `_build/.../*.bat` and `_build/.../tests-*.bat` are generated artifacts after build.
- `.vscode/tasks.json` wraps official repo commands for developer convenience.

Future root `scripts/` should be project-owned helper tooling only. It should provide safe,
explicit wrappers and utilities for validation, hygiene checks, documentation support, local
developer workflows, and controlled cleanup. It must not replace Kit App Template tooling, hide
unsafe behavior behind convenience commands, or become a home for reusable library code,
backend orchestration, tests, source extensions, generated artifacts, secrets, or runtime outputs.

This document is a design contract only. It does not create `scripts/`, edit existing scripts,
run scripts, run build/launch/test commands, stage, commit, or push.

## 2. Current Script and Tooling Inventory

Current root-level tooling-like files:

| Path | Current role | Classification |
| --- | --- | --- |
| `repo.bat` | Windows entrypoint into Packman Python and `tools/repoman/repoman.py` | Kit tooling, not root `scripts/` |
| `repo.sh` | Linux/macOS shell entrypoint into Packman Python and `tools/repoman/repoman.py` | Kit tooling, not root `scripts/` |
| `premake5.lua` | Root Kit/Premake build configuration; defines `my_own_software.kit` app build | Kit build configuration |
| `repo.toml` | Repo, build, launch, package, and extension discovery configuration | Kit workflow configuration |
| `repo_tools.toml` | Repo tool configuration | Kit workflow configuration |
| `tools/` | Packman, Repoman, package wrappers, dependency manifests | Kit-managed tooling |
| `templates/` | Kit App Template scaffold source | Template/scaffolding |
| `.vscode/tasks.json` | IDE task wrappers for template, build, launch, test, package | Developer configuration |
| `.vscode/template_builder.py` | Template generation helper used by VS Code task | Template/developer helper |
| `.github/workflows/create_templates.py` | Template workflow helper | Template/GitHub workflow helper |
| `tools_tree.txt` | Generated repository analysis dump | Temporary analysis dump, should stay ignored |

Current extension-local build files:

| Path pattern | Current role | Classification |
| --- | --- | --- |
| `source/extensions/*/premake5.lua` | Per-extension Premake registration | Extension-local Kit build configuration |

Current generated script-like artifacts:

| Path pattern | Current role | Classification |
| --- | --- | --- |
| `_build/windows-x86_64/debug/*.bat` | Generated Kit app/test launch wrappers | Generated build artifact |
| `_build/windows-x86_64/release/*.bat` | Generated Kit app/test launch wrappers | Generated build artifact |
| `_build/windows-x86_64/release/dev/repo.bat` | Generated dev-bundle repo wrapper | Generated build artifact |
| `_build/windows-x86_64/*/tests-*.bat` | Generated extension/app test wrappers | Generated build artifact |

There is currently no root-level `scripts/` directory.

## 3. Architectural Role of Future `scripts/`

Future root `scripts/` should contain project-owned executable helper scripts that make common
developer and validation workflows safer and more repeatable.

`scripts/` should be used for:

- developer convenience wrappers
- repository validation wrappers
- repository hygiene checks
- safe build/launch command wrappers around `repo.bat` or `repo.sh`
- safe cleanup helpers with dry-run behavior
- EnergyPlus environment inspection helpers
- data management helpers that do not own datasets
- documentation indexing or diagram generation helpers
- Codex workflow helpers
- read-only Git inspection helpers

`scripts/` should not be used for:

- Kit app descriptors or extensions
- extension startup/runtime code
- reusable library code
- backend service orchestration
- long-running simulation/calibration/training workflows
- tests that assert correctness
- generated `_build` launch/test scripts
- runtime outputs, logs, datasets, trained models, or simulation runs
- vendor binaries
- secrets or local machine configuration
- automatic commit, push, history rewrite, or force-push workflows

The short rule is: scripts are explicit entrypoints and glue. If code becomes reusable, move it
to future `packages/`. If it becomes a long-running workflow or service, move it to future
`backend/`. If it asserts behavior, move it to tests.

## 4. Proposed Future Layout

When `scripts/` is eventually created by a future ticket, the recommended structure is:

```text
scripts/
  README.md
  dev/
  validation/
  repo_hygiene/
  build/
  launch/
  cleanup/
  energyplus/
  data/
  docs/
  codex/
  git/
```

### `scripts/README.md`

Index of available scripts, required runtime, supported platforms, examples, safety behavior,
and whether each script is read-only, writes generated files, or can delete files.

### `scripts/dev/`

Developer convenience entrypoints that do not belong to Kit itself. Examples: environment
inspection, local path diagnostics, or command discovery. These scripts should stay shallow and
should not duplicate backend/package logic.

### `scripts/validation/`

Manual validation wrappers for reproducibility workflows, clean-clone checks, smoke-test command
sequences, or pre-ticket validation. These may call `repo.bat build`, `repo.bat launch`, or
future test commands only when explicitly documented.

### `scripts/repo_hygiene/`

Read-only checks for ignored/generated artifacts, forbidden tracked files, source visibility,
large file detection, local path detection, and secret-pattern scanning. These scripts should be
safe to run before commits and future CI.

### `scripts/build/`

Thin wrappers around official Kit App Template build commands. These may standardize command
arguments or collect logs, but `repo.bat build` / `repo.sh build` remain authoritative.

### `scripts/launch/`

Thin wrappers around official Kit launch commands for known app names and smoke modes. These
must document whether they start GUI Kit, headless Kit, or generated `_build` wrappers.

### `scripts/cleanup/`

High-risk utilities for removing generated artifacts, caches, pycache, or runtime directories.
Cleanup scripts must be dry-run by default and must require explicit confirmation or flags before
deleting anything.

### `scripts/energyplus/`

Helpers for inspecting local EnergyPlus configuration, validating environment variables, locating
an executable, or creating approved example config templates. Real EnergyPlus execution belongs
in future `backend/` once that boundary exists.

### `scripts/data/`

Data governance helpers, such as metadata validation, manifest checks, or size/privacy scans.
These scripts must not silently modify curated data.

### `scripts/docs/`

Documentation support utilities, such as generating a docs index, checking internal links, or
rendering diagrams. These scripts must not overwrite hand-authored architecture contracts unless
the task explicitly asks for it.

### `scripts/codex/`

Codex workflow helpers for repeatable read-only inspections, ticket validation summaries, or
policy checks. These must remain explicit and auditable.

### `scripts/git/`

Read-only or staging-review Git helpers, such as listing staged files, ignored files, or forbidden
paths. These scripts must not run `git commit`, `git push`, `git reset --hard`, history rewrites,
or force push.

## 5. Boundary Policy

### `scripts/` vs `tools/`

`tools/` is Kit App Template tooling. It contains Packman, Repoman, dependency manifests, and
template-provided command infrastructure. It should be treated as Kit-managed unless a future
Kit-maintenance ticket explicitly scopes a change.

`scripts/` should be project-owned helpers. Scripts may call `repo.bat`, `repo.sh`, or `tools/`
entrypoints, but they must not fork, replace, or mutate Kit tooling.

### `scripts/` vs `backend/`

`backend/` is for service/process orchestration, EnergyPlus execution, batch jobs, calibration,
dataset generation, surrogate training, and control/RL workflows. Scripts may call backend
entrypoints once they exist, but they should not contain core backend business logic.

### `scripts/` vs `packages/`

`packages/` is for reusable, headless, testable Python library code. Scripts may import packages,
but packages must not import scripts. If a helper grows reusable parsing, validation, or domain
logic, that logic should move into a package and leave the script as an entrypoint.

### `scripts/` vs `tests/`

Scripts may invoke tests or prepare test environments. Tests assert correctness and should live
in root `tests/`, package-local tests, backend tests, or extension-local tests. Scripts must not
replace tests or hide failed assertions.

### `scripts/` vs `source/extensions`

`source/extensions/` is Kit-integrated product source-of-truth. Scripts must not contain extension
startup classes, UI panels, `extension.toml`, Kit app configuration, or Omniverse runtime code.
Extensions may call package/backend APIs, not random root scripts.

### `scripts/` vs `docs/`

Docs are source-of-truth narrative and contracts. Scripts may generate indexes, diagrams, or
validation summaries only when explicitly requested. Generated docs should be reviewed before
commit.

### `scripts/` vs Generated `_build/*.bat`

Generated `_build` batch files are build artifacts. They are not source-of-truth, must stay
ignored, must not be edited by hand, and must not be copied into `scripts/`.

## 6. Safety Policy

All future scripts should follow these rules:

- Destructive actions must be dry-run by default.
- Deletion requires explicit confirmation or an explicit destructive flag.
- Scripts must list target paths before deleting or moving anything.
- Scripts must validate that resolved paths stay inside intended workspace roots.
- Scripts must handle spaces in Windows paths correctly.
- Scripts must avoid shell-string command construction when structured process APIs are available.
- Scripts must not execute arbitrary user-provided shell commands.
- Scripts must not contain secrets, tokens, credentials, or local-only private configuration.
- Scripts must not hardcode local absolute paths such as user profiles, AppData, or `C:\temp`.
- Scripts must write outputs only to documented output roots.
- Scripts must report generated or modified files.
- Scripts must return nonzero exit codes on failure.
- Scripts must separate read-only checks from write/delete operations.
- Scripts must make long-running or GPU/GUI behavior explicit.

Cleanup scripts require extra caution:

- Never delete source by pattern alone.
- Treat `_build`, `_repo`, `_compiler`, `runs`, `outputs`, `__pycache__`, `.pyc`, logs, and
  owner-decision files as separate cleanup classes.
- Never delete root owner-decision files without explicit owner approval.
- Never delete vendor/external resources without a dedicated decision ticket.
- Prefer producing a cleanup plan/report before performing cleanup.

## 7. Cross-Platform Policy

This project is Windows-first in practice because current Omniverse Kit validation uses
`repo.bat`, Windows paths, and generated Windows batch wrappers. PowerShell scripts are acceptable
for Windows-specific developer workflows.

Python scripts are preferred when the logic should be cross-platform, testable, and reused by
Windows/Linux wrappers. `.bat` wrappers may call PowerShell or Python for convenience. `.sh`
wrappers should be added only when Linux support is actively validated.

Line-ending policy should be explicit:

- `.ps1`, `.bat`, and `.cmd` may use CRLF.
- `.sh` should use LF.
- Python should be compatible with both where possible.

Scripts must not imply Linux support until the workflow is validated on Linux.

## 8. Kit App Template Tooling Relationship

`repo.bat` and `repo.sh` remain the official Kit App Template entrypoints. Future scripts may
wrap these commands, but must not replace them.

Required policy:

- Use `repo.bat build` / `repo.sh build` as the canonical build path.
- Use `repo.bat launch` / `repo.sh launch` as the canonical launch path.
- Use `repo.bat test` / `repo.sh test` as the canonical Kit test path when applicable.
- Document when a script calls build, launch, package, or test commands.
- Do not edit generated `_build/*.bat` scripts.
- Do not commit generated `_build/*.bat` scripts.
- Do not mutate `_build`, `_repo`, or `_compiler` except through official repo tooling or an
  explicitly approved cleanup ticket.
- Do not introduce scripts that depend on generated wrappers existing before build unless the
  script checks for that precondition and explains how to build.

## 9. Backend, Package, Test, and Docs Relationship Policy

Scripts should remain thin orchestration entrypoints:

- A script may call future backend commands but should not own backend workflow logic.
- A script may import future packages but should not become a package substitute.
- A script may run tests but should not encode assertions that belong in test files.
- A script may generate documentation support artifacts but should not overwrite hand-authored
  docs without explicit scope.
- A script may produce validation logs or summaries, but promoted validation reports belong in
  docs after review.

## 10. Cleanup, EnergyPlus, and Git Helper Policy

### Cleanup

Cleanup is high-risk and should be introduced only by dedicated tickets. Future cleanup scripts
must support dry-run, clear target listing, explicit deletion confirmation, separate cleanup
classes, and post-run summaries.

### EnergyPlus

EnergyPlus scripts may help inspect the local environment:

- check whether an EnergyPlus executable path is configured
- validate an environment variable or config file
- report executable version if requested
- create approved example config templates

Real EnergyPlus execution, batch simulation, output collection, and subprocess safety belong in
future `backend/`. Scripts must not hardcode EnergyPlus paths or run long simulations unless the
user explicitly requests execution and the script makes output locations clear.

### Git

Because repository history is owner-controlled, future Git helper scripts must be conservative:

- May run read-only `git status`, `git diff`, `git ls-files`, and `git check-ignore`.
- May list staged files and forbidden staged paths.
- Must not run `git commit` automatically.
- Must not run `git push` automatically.
- Must not rewrite history.
- Must not force push.
- Must not hide generated/local files by staging broad patterns.

Git operations remain manual by default.

## 11. Current Artifact Classification

| Artifact | Classification | Recommendation |
| --- | --- | --- |
| `repo.bat` | Kit tooling | Keep at root; official Windows entrypoint; do not move to `scripts/` |
| `repo.sh` | Kit tooling | Keep at root; official shell entrypoint; do not move to `scripts/` |
| `premake5.lua` | Kit build configuration | Keep at root; not a script utility |
| `repo.toml` | Kit workflow configuration | Keep at root; not a script utility |
| `repo_tools.toml` | Kit tooling configuration | Keep at root |
| `source/extensions/*/premake5.lua` | Extension build configuration | Keep extension-local |
| `tools/` | Kit-managed tooling | Inspect/edit only under explicit Kit tooling tickets |
| `templates/` | Kit template/scaffolding | Keep as template-managed source |
| `.vscode/tasks.json` | Developer IDE task config | Keep as developer config; may call repo tooling |
| `.vscode/template_builder.py` | Template helper | Keep under `.vscode` unless future template policy changes |
| `.github/workflows/create_templates.py` | Template workflow helper | Keep under GitHub workflow/template ownership |
| `_build/windows-x86_64/*/*.bat` | Generated build artifact | Ignore; do not edit or commit |
| `_build/windows-x86_64/*/tests-*.bat` | Generated Kit test wrapper | Ignore; may be invoked manually after build, not source-of-truth |
| `tools_tree.txt` | Temporary analysis dump | Keep ignored; do not commit |
| Root `00_*.txt` context files | Owner-decision documentation/workflow notes | Not scripts; owner review before moving/committing |
| Future backend entrypoints | Backend-owned execution entrypoints | Keep in `backend/`; scripts may wrap |
| Future validation wrappers | Project helper scripts | Candidate for `scripts/validation/` |
| Future cleanup helpers | High-risk project helper scripts | Candidate for `scripts/cleanup/` with dry-run and approval |

## 12. Codex Access Policy

Codex may create or edit scripts only when a task explicitly allows script changes.

Required behavior for future script tasks:

- Explain script purpose and safety behavior before editing.
- Use dry-run defaults for cleanup or destructive workflows.
- Avoid broad filesystem mutations.
- Avoid automating commits or pushes.
- Do not run cleanup scripts unless explicitly authorized.
- Do not run long simulations or EnergyPlus workflows unless explicitly authorized.
- Report commands run and files generated.
- Run relevant tests or validation when modifying executable scripts.
- Do not edit Kit-managed `tools/` or generated `_build` scripts unless the ticket explicitly
  targets those areas.

## 13. Naming and Implementation Conventions

Recommended conventions for future scripts:

- Use lowercase snake_case filenames.
- Use clear verbs: `check_`, `validate_`, `list_`, `generate_`, `cleanup_`.
- Prefer `--dry-run` and make it default for destructive workflows.
- Prefer `--yes` or `--force` only for explicit destructive confirmation.
- Prefer `--output-dir` over hardcoded paths.
- Print concise summaries and machine-readable output where useful.
- Include `--help`.
- Keep scripts small; move reusable logic to packages.
- Add README usage examples before relying on a script in a workflow.

## 14. Open Decisions

- Whether to create `scripts/` now or wait until the first approved script exists.
- Whether primary future scripts should be PowerShell, Python, or paired wrappers.
- Whether to standardize on a common CLI library for Python scripts.
- Whether script logs should go to `runs/`, `outputs/tmp`, or a dedicated local log root.
- Whether repo hygiene scripts should later become CI checks.
- Whether cleanup scripts should ever support non-interactive deletion.
- Whether EnergyPlus environment validation belongs in `scripts/energyplus/` before backend exists.
- Whether Codex helper scripts should be public repo assets or local-only developer utilities.

## 15. Risks

- Duplicating Kit App Template behavior in project scripts could drift from upstream tooling.
- Cleanup helpers can delete important local or owner-decision files if path validation is weak.
- Git helper scripts can create false confidence if they hide staged/generated files.
- PowerShell-only scripts may limit future Linux validation.
- Python scripts may depend on an interpreter that differs from Kit/Packman Python unless documented.
- EnergyPlus helpers can become backend logic if not kept narrow.
- Documentation-generation scripts can overwrite architecture contracts if not scoped carefully.
- Convenience wrappers can obscure whether `repo.bat`, generated `_build` wrappers, or backend code
  is actually being executed.

## 16. Validation Commands Used for This Contract

Read-only commands used while preparing this document:

```powershell
git status --short
Get-ChildItem -Force | Where-Object { $_.Name -match "scripts|tools|templates|repo\.bat|repo\.sh|premake5\.lua" }
Test-Path scripts
Get-ChildItem tools -Recurse -Depth 2 -Force | Select-Object FullName,Mode,Length
Get-ChildItem -Recurse -File -Force | Where-Object { $_.Extension -match "\.(ps1|bat|cmd|sh|py|lua|json)$" } | Select-Object FullName,Length
rg -n "script|scripts|repo\.bat|repo\.sh|premake|cleanup|dry-run|build|launch|test|codex|git commit|git push|EnergyPlus|subprocess" docs source tools templates README.md repo.toml premake5.lua
Get-ChildItem source\extensions -Recurse -Filter premake5.lua -Force | Select-Object FullName,Length
Get-ChildItem _build -Recurse -File -Force -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(bat|cmd|ps1|sh)$" } | Select-Object FullName,Length
Get-Content repo.bat | Select-Object -First 80
Get-Content repo.sh | Select-Object -First 80
Get-Content .vscode\tasks.json
Get-Content premake5.lua
```

## 17. Recommended Next Ticket

Recommended next ticket: design the future `config/` or `schemas/` repository structure, depending
on whether the next architectural priority is local/runtime configuration governance or shared
data/API contract governance.
