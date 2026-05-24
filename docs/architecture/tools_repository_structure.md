# Tools Repository Structure Contract

Status: proposed architecture contract  
Scope: existing root `tools/` policy only  
Date: 2026-05-24

## 1. Executive Summary

The current `tools/` directory is inherited from the NVIDIA Omniverse Kit App Template. It is part
of the committed Kit toolchain source used by `repo.bat`, `repo.sh`, `repo.toml`, `repo_tools.toml`,
and `premake5.lua`.

Current `tools/` contains:

- Packman bootstrap/runtime wrappers under `tools/packman/`.
- Repoman launch/package/bootstrap helpers under `tools/repoman/`.
- Packman dependency manifests under `tools/deps/`.
- lightweight package wrappers and version metadata.

`tools/` should be treated as Kit/template-managed tooling, not as a general project utility
folder. Future project-owned helper scripts should go under future `scripts/`, not into current
Kit-managed `tools/`, unless a future explicit tooling ticket approves a deliberate exception.

This document is a design contract only. It does not edit `tools/`, create tool folders, move files,
delete files, run build/launch/tests/cleanup/simulations, stage, commit, or push.

## 2. Current `tools/` Structure

Observed current structure:

```text
tools/
  VERSION.md
  package.bat
  package.sh
  deps/
    host-deps.packman.xml
    kit-sdk-deps.packman.xml
    kit-sdk.packman.xml
    pip.toml
    repo-deps.packman.xml
    user.toml
  packman/
    config.packman.xml
    packman
    packman.cmd
    packmanconf.py
    python.bat
    python.sh
    bootstrap/
      configure.bat
      download_file_from_url.ps1
      fetch_file_from_packman_bootstrap.cmd
      generate_temp_file_name.ps1
      generate_temp_folder.ps1
      install_package.py
  repoman/
    launch.py
    package.py
    repoman.py
    repoman_bootstrapper.py
    __pycache__/
```

Tracked `tools/` files include `tools/VERSION.md`, dependency manifests, Packman wrappers,
Packman bootstrap scripts, and Repoman Python helpers.

Ignored/generated state observed under tooling:

- `tools/repoman/__pycache__/` is ignored cache state and should not be committed.
- `_repo/` is ignored generated dependency/tool state.
- `_build/` is ignored generated build/runtime state.
- `_compiler/` is local/generated compiler/tool state; the command reported a missing nested
  `_compiler/current/` path while checking ignored status, which is a local filesystem detail, not
  a source issue.

## 3. Architectural Role of Current `tools/`

Current `tools/` is Kit App Template tooling infrastructure.

It is:

- Kit/template-managed.
- Required by `repo.bat` and `repo.sh`.
- Required for Packman dependency bootstrapping.
- Required for Repoman command dispatch.
- Part of the repository's build/launch/package/test workflow.
- High-impact if changed.

It is not:

- general product source.
- a project-owned utility/script area.
- a backend workflow area.
- a reusable library package area.
- a test suite area.
- a runtime output/cache area.

Default policy: inspect-only for normal product work. Edits require an explicit Kit tooling ticket,
a clear rationale, and clean-clone validation.

## 4. What Belongs in `tools/`

The following belong in current `tools/`:

- third-party/toolchain wrappers inherited from Kit App Template
- Packman bootstrap and runtime wrappers
- Repoman command dispatch helpers
- dependency manifests consumed by repo tooling
- template tooling required by `repo.bat` / `repo.sh`
- project-agnostic repo tooling inherited from the template
- version metadata used by packaging/tooling

Future additions to `tools/` should be rare and must be justified as toolchain infrastructure, not
project convenience tooling.

## 5. What Does Not Belong in `tools/`

Do not put these in current `tools/`:

- project-owned helper scripts
- Codex workflow helpers
- repository hygiene scripts
- cleanup scripts
- backend orchestration
- EnergyPlus execution workflows
- package/library code
- domain logic
- tests
- test fixtures
- source extensions
- app `.kit` descriptors
- generated `_build` wrappers
- runtime outputs
- generated artifacts
- local developer config
- secrets
- experiments or one-off utilities
- datasets, examples, references, notebooks, or reports

If the goal is project convenience, use future `scripts/`. If the goal is long-running execution,
use future `backend/`. If the goal is reusable logic, use future `packages/`.

## 6. Boundary Policy

### `tools/` vs `scripts/`

`tools/` is template/toolchain-owned. Future `scripts/` is project-owned helper tooling.

Rules:

- Scripts may call `repo.bat`, `repo.sh`, or stable tooling commands.
- Scripts must not mutate `tools/` as a side effect.
- Avoid adding project helper scripts to `tools/`.
- Prefer wrappers under `scripts/` over editing inherited Kit tooling.
- Cleanup and repo hygiene helpers belong in `scripts/`, not `tools/`.

### `tools/` vs `backend/`

`backend/` owns long-running workflow/process orchestration. `tools/` must not become backend.

Rules:

- EnergyPlus runners do not belong in current `tools/`.
- Batch simulation, calibration, dataset generation, surrogate training, RL/control, and worker
  orchestration belong in future `backend/`.
- Backend may use `repo.bat` or tooling only if the dependency is explicit and documented.
- Backend must not import private `tools/repoman` internals as application logic.

### `tools/` vs `packages/`

`packages/` contains reusable Python libraries. `tools/` contains executable/toolchain
infrastructure.

Rules:

- No domain logic should live in `tools/`.
- Packages should not import from `tools/` unless a future explicit policy approves a stable API.
- Shared validators, parsers, and models belong in packages, not `tools/`.
- Tooling code may remain imperative and workflow-oriented because it supports the Kit repo toolchain.

### `tools/` vs `tests/`

Tests assert correctness. `tools/` may provide template-owned test entrypoints only as part of the
Kit workflow.

Rules:

- Generated `_build/.../tests-*.bat` wrappers are build artifacts, not `tools/` source.
- Future repo hygiene tests belong under future `tests/` or `scripts/`, not current `tools/`.
- Do not hide test assertions inside tooling scripts.

### `tools/` vs `templates/`

`templates/` contains scaffold input. `tools/` may render, select, or use templates through repo
tooling.

Rules:

- Template content remains in `templates/`.
- Tooling that modifies templates is high-impact.
- Template-generation behavior changes require explicit validation.
- Do not move templates into `tools/`.

### `tools/` vs `_repo`, `_build`, and `_compiler`

`tools/` is committed toolchain source. `_repo`, `_build`, and `_compiler` are generated,
runtime, dependency, build, or local tool cache outputs.

Rules:

- Do not edit `_repo`, `_build`, or `_compiler` as if they were source.
- Do not commit generated tool cache state.
- Do not copy generated scripts from `_build` into `tools/`.
- If generated output is wrong, inspect source config/tooling and fix the source under an explicit
  ticket.

## 7. Maintenance and Update Policy

Changes to `tools/` can affect every build, launch, package, and template operation.

Policy:

- Preserve upstream Kit App Template compatibility.
- Avoid modifying inherited Packman/Repoman tooling casually.
- Prefer `scripts/` wrappers for project-specific workflows.
- Require explicit rationale for any `tools/` edit.
- Document local modifications if any are made.
- Validate changes from a clean clone.
- Run appropriate `repo.bat --help`, build, launch, and package/test smoke checks when the change
  affects those paths and the ticket permits execution.
- Expect upstream merge conflicts if Kit-managed tooling is customized.
- Do not use generated `_repo` or `_build` files as a source of truth for tool edits.

Recommended default stance: treat `tools/` as read-only vendor/toolchain source unless the ticket
explicitly targets Kit tooling.

## 8. Security Policy

Tooling can execute processes and download dependencies, so changes are security-sensitive.

Rules:

- Do not add arbitrary shell command execution.
- Do not add secrets, tokens, or credentials.
- Do not hardcode machine-specific paths.
- Do not weaken dependency/download verification.
- Review any download URL, bootstrap behavior, cache path, or dependency manifest change carefully.
- Treat user-provided paths as untrusted.
- Keep process invocation explicit.
- Avoid broad filesystem mutation from tooling.
- Do not change Packman/Repoman bootstrap behavior without understanding dependency resolution and
  offline/cache implications.

## 9. Codex Access Policy

Codex may inspect `tools/` freely for architecture, build, and dependency analysis.

Codex must not:

- edit `tools/` unless a ticket explicitly targets Kit tooling.
- run destructive tooling commands.
- modify Packman/Repoman behavior casually.
- add project helper scripts to `tools/`.
- patch `_repo`, `_build`, or `_compiler` generated state to fix source issues.
- commit pycache or generated tool cache state.

Codex should:

- prefer future `scripts/` for project-owned wrappers.
- report any proposed tooling changes before editing.
- list validation required for any `tools/` modification.
- preserve upstream compatibility unless a ticket explicitly accepts divergence.

## 10. Current Artifact Classification

| Artifact | Classification | Policy |
| --- | --- | --- |
| `tools/` | Kit-managed/toolchain source | Inspect normally; edit only under explicit Kit tooling ticket |
| `tools/deps/*.packman.xml` | Packman dependency manifests | High-impact; edit only with dependency/tooling rationale |
| `tools/deps/pip.toml` | Optional Python dependency manifest | High-impact; edit only with dependency policy and validation |
| `tools/deps/user.toml` | User/dependency config copied during prebuild | Treat carefully; avoid local secrets |
| `tools/packman/` | Packman bootstrap/runtime tooling | Inspect-only by default; do not modify casually |
| `tools/packman/bootstrap/` | Download/bootstrap helpers | Security-sensitive; edit only with explicit review |
| `tools/repoman/` | Repoman command helpers | Inspect-only by default; edit only with explicit review |
| `tools/repoman/__pycache__/` | Cache | Ignored; do not commit; cleanup only under cleanup ticket |
| `tools/package.bat`, `tools/package.sh` | Tool wrappers | Kit/toolchain wrappers; edit only under explicit tooling ticket |
| `tools/VERSION.md` | Tool/package version metadata | Tooling/package metadata; edit only with packaging/version rationale |
| `repo.bat` | Official Windows repo entrypoint | Kit tooling; keep at root; edit only under explicit tooling ticket |
| `repo.sh` | Official shell repo entrypoint | Kit tooling; keep at root; edit only under explicit tooling ticket |
| `repo_tools.toml` | Repo tool config | Tooling config; high-impact |
| `repo.toml` | Repo/build/launch/package config | Project-owned Kit workflow config; edit only under scoped config/build tickets |
| `premake5.lua` | Root Kit build config | Project-owned Kit build config; edit only under scoped build/source tickets |
| `source/extensions/*/premake5.lua` | Extension build config | Extension-local Kit build config |
| `templates/` | Kit template/scaffolding source | Template-managed; edit only under template tickets |
| `_repo/` | Generated dependency/tool state | Ignored; do not commit/edit as source |
| `_build/` | Generated build/runtime state | Ignored; do not commit/edit as source |
| `_compiler/` | Local/generated compiler/tool state | Ignore/local; do not commit/edit as source |
| `_build/**/*.bat` | Generated launch/test wrappers | Generated artifacts; do not commit or edit |
| future `scripts/` | Project-owned helper scripts | Preferred destination for project wrappers/utilities |

## 11. Open Decisions

- Whether `tools/` should be formally treated as read-only vendor/toolchain source.
- Whether any project-owned tool should ever live in `tools/`, or whether `scripts/` should fully
  isolate project helpers.
- How to update inherited tooling from upstream NVIDIA Kit App Template.
- How to document local modifications if a future ticket changes Packman/Repoman files.
- Whether dependency manifests should be owned by platform/tooling tickets only.
- Whether `tools/deps/user.toml` should remain empty or get an explicit local-config policy.
- How future CI should validate tooling without running GUI Kit.
- Whether generated `tools/repoman/__pycache__/` should be cleaned in a future cleanup ticket.

## 12. Risks

- Editing Packman/Repoman can break clean clone bootstrap.
- Tool changes can silently affect build, launch, test, packaging, and template generation.
- Upstream merge compatibility becomes harder if inherited tooling diverges.
- Dependency/download changes can introduce security and reproducibility risk.
- Project helper scripts in `tools/` would blur ownership with Kit-managed tooling.
- Generated `_repo`/`_build` files can be mistaken for source.
- Pycache under `tools/repoman` can pollute local state if ignored policy is not enforced.
- Hardcoded local paths or secrets in tooling would be high-risk in a public repo.

## 13. Validation Commands Used for This Contract

Read-only commands used while preparing this document:

```powershell
git status --short
Get-ChildItem tools -Recurse -Depth 4 -Force | Select-Object FullName,Mode,Length
Get-ChildItem -Force | Where-Object { $_.Name -match "repo\.bat|repo\.sh|repo_tools\.toml|repo\.toml|premake5\.lua|tools|templates|_repo|_build|_compiler" }
Get-ChildItem source\extensions -Recurse -Filter premake5.lua -Force | Select-Object FullName,Length
rg -n "packman|repoman|repo_tools|repo\.bat|repo\.sh|tools/|templates|_repo|_build|_compiler|premake|download|dependency|container|package" tools templates docs README.md repo.toml repo_tools.toml premake5.lua
git ls-files tools
git status --ignored --short tools _repo _build _compiler
Get-Content repo_tools.toml
Get-Content repo.bat | Select-Object -First 80
Get-Content repo.sh | Select-Object -First 80
```

## 14. Recommended Next Ticket

Recommended next ticket: design the future `config/` repository structure. The remaining open
repository architecture questions now center on committed example configuration, ignored local
configuration, EnergyPlus executable paths, backend job settings, and environment policy.
