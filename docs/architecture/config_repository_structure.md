# Config Repository Structure Contract

Status: proposed architecture contract  
Scope: future root `config/` structure only  
Date: 2026-05-24

## 1. Executive Summary

This repository does not currently have a root-level `config/`, `.env`, or `.env.example`. Existing
configuration already lives in several Kit/template-specific locations:

- `repo.toml` and `repo_tools.toml` configure the Kit App Template repo tooling.
- `premake5.lua` configures Kit/Premake build behavior.
- `source/apps/my_own_software.kit` configures the active Kit application.
- `source/extensions/*/config/extension.toml` files configure extension metadata and dependencies.
- `.vscode/` contains developer IDE settings, tasks, launch configuration, and template helper code.
- `tools/deps/*.toml` configures Packman/pip dependency pulls.
- `_build/**/*.toml`, `_build/**/*.json`, and generated `.kit` files are generated artifacts.

Future root `config/` should be used only for project-level configuration that is not Kit app
composition, not extension metadata, not IDE settings, not generated state, and not local secrets.
It should host public-safe example configuration, non-secret defaults, validation config,
environment-variable conventions, and future backend/EnergyPlus configuration examples when those
workflows exist.

This document is a design contract only. It does not create `config/`, create `.env`, add config
files, edit existing configs/source, run build/launch/tests/EnergyPlus/simulations, stage, commit,
or push.

## 2. Current Config-Like Inventory

Current configuration-like files and areas:

| Path or area | Current role | Classification |
| --- | --- | --- |
| `repo.toml` | Kit App Template repo/build/launch/package/template configuration | Kit workflow config |
| `repo_tools.toml` | Repo tool command override config | Kit tooling config |
| `premake5.lua` | Root build definition; defines active app build | Kit/Premake build config |
| `source/apps/my_own_software.kit` | Active app descriptor, dependencies, settings, generated version lock | Kit app config/source-of-truth |
| `source/extensions/*/config/extension.toml` | Extension package metadata, dependencies, Python modules | Kit extension manifests |
| `.vscode/launch.json` | VS Code debug attach config on `localhost:3000` | Developer config |
| `.vscode/tasks.json` | VS Code wrappers for repo build/launch/test/package/template | Developer tooling config |
| `.vscode/settings.json` | Shared IDE analysis/file settings, including generated `_build` paths | Developer config with generated path references |
| `.vscode/template_builder.py` | Template helper script | Developer/template tooling |
| `tools/deps/pip.toml` | Packman/pip dependency manifest examples | Kit/tool dependency config |
| `tools/deps/user.toml` | Empty dependency/user config copied during prebuild | Kit/tool dependency config; keep secrets out |
| `source/rendered_template_metadata.json` | Untracked template metadata | Generated/template metadata; should not be committed without decision |
| `_build/**/*.toml`, `_build/**/*.json`, `_build/apps/*.kit` | Generated repo/build/dev config | Generated artifacts |
| hardcoded `C:/temp`, `C:/tmp` paths | Transitional allowed roots and IDF/DXF output behavior | Source behavior to replace later |
| `NVIDIA_API_KEY` environment use | LLM provider credential lookup | Local-only environment variable |

There is no committed root config area yet.

## 3. Architectural Role of Future `config/`

Future root `config/` should contain project-level configuration artifacts that are:

- public-safe
- non-secret
- intentionally shared
- not Kit app descriptors
- not extension manifests
- not IDE settings
- not generated outputs
- not local machine state

Use future `config/` for:

- committed example configuration
- safe defaults for project-owned workflows
- environment variable documentation
- `.env.example` with placeholders only, if approved
- EnergyPlus example/local config templates
- backend job config examples
- validation config
- logging config templates
- public-safe runtime policy examples

Do not use `config/` for:

- `repo.toml`, `repo_tools.toml`, or Premake config
- app `.kit` descriptors
- extension `extension.toml` manifests
- `.vscode` IDE settings
- real `.env` files
- secrets
- API keys or provider credentials
- MQTT credentials
- local absolute paths
- user profile paths
- real building/customer endpoints
- generated `_build` config
- runtime run manifests
- output metadata
- schema definitions
- backend implementation code

The short rule is: root `config/` is for shared project-level configuration examples/defaults, not
for Kit source configuration or local secrets.

## 4. Proposed Future Layout

When `config/` is eventually created by a future ticket, the recommended structure is:

```text
config/
  README.md
  examples/
  defaults/
  local/
  energyplus/
  backend/
  validation/
  logging/
```

### `config/README.md`

Explains committed vs local-only configuration, supported formats, environment variables, security
rules, validation commands, and where Kit configuration remains.

### `config/examples/`

Public-safe example configuration files. These should use placeholders, relative paths, or
environment-variable names. They should not be directly mutated by runtime jobs.

### `config/defaults/`

Committed default settings for project-owned workflows only. Defaults must be safe in a public repo
and must not duplicate Kit app or extension configuration.

### `config/local/`

Reserved location for ignored local-only config if a future `.gitignore` policy permits it. This
folder should not be committed except perhaps a README or `.gitkeep`, and only after approval.

### `config/energyplus/`

EnergyPlus example configuration and local config templates: executable path variable names,
weather root placeholders, run/output root placeholders, version policy, and container/service
options. Real local paths belong in ignored files.

### `config/backend/`

Project-level backend config examples or defaults that are shared across backend services. Deep
backend-internal config may later live under `backend/config/`.

### `config/validation/`

Validation tool configuration, such as allowed roots, repo hygiene policy knobs, schema validation
config, or smoke-test target definitions. Executable validators belong in `scripts/` or tests.

### `config/logging/`

Logging format and level defaults for project-owned backend/scripts workflows. Kit logging remains
Kit-configured through app `.kit` settings unless explicitly migrated.

## 5. Boundary Policy

### `config/` vs `repo.toml` and `repo_tools.toml`

`repo.toml` and `repo_tools.toml` are Kit App Template repo-tool configuration. They should stay at
the repository root and remain governed by Kit tooling/build tickets. Root `config/` must not
duplicate repo build, launch, package, template, dependency, or repo tool settings.

### `config/` vs app `.kit` files

App `.kit` files remain under `source/apps/`. They define Kit app dependencies, app settings,
extension folders, window settings, persistent app settings, and generated version-lock blocks.
Root `config/` must not become an alternate app composition mechanism.

### `config/` vs extension `extension.toml`

Extension manifests remain under `source/extensions/<extension>/config/extension.toml`. They define
extension package metadata, dependencies, and Python module registration. Root `config/` must not
duplicate extension metadata.

### `config/` vs `.vscode/`

`.vscode/` is developer tooling config. Tasks, launch attach settings, editor settings, and
template-builder helpers stay there. Root `config/` should not contain IDE configuration.

### `config/` vs `backend/config`

Root `config/` should hold shared examples/defaults and cross-cutting project config. Future
`backend/config/` may hold backend-service-local defaults, loader code, or internal service config.
Backend may consume root config examples, but backend implementation belongs in `backend/`.

### `config/` vs `schemas/`

`schemas/` defines machine-readable contracts. `config/` contains config instances or examples.
Config schemas may live under `schemas/`; config examples should validate against them.

### `config/` vs local `.env`

`.env` files are local-only and must not be committed. `.env.example` may be committed only with
placeholder values and documentation. Environment variable names may be documented in `config/README`
or example files.

## 6. Committed vs Local-Only Configuration Policy

Committed config must be:

- public-safe
- non-secret
- deterministic
- reviewed
- documented
- portable across machines
- free of user profile paths
- free of private endpoints
- free of real credentials

Local-only config must be:

- ignored by Git
- kept out of source/app/extension config
- kept out of committed docs except sanitized examples
- reviewed before promotion to committed examples

Policy:

- `.env.example` is allowed only with placeholders.
- `.env` must not be committed.
- `.env.local` must not be committed.
- No API keys, tokens, passwords, LLM provider keys, MQTT credentials, or customer endpoints.
- No committed `C:/Users/...`, private network shares, or personal directories.
- Local service URLs require review before commit; `localhost` examples may be acceptable when
  clearly illustrative.

## 7. EnergyPlus Configuration Policy

Future EnergyPlus config should be explicit and local-safe.

Config concerns:

- executable path
- EnergyPlus version
- weather/EPW root
- default run root
- output root
- container image or external service endpoint
- timeout and resource limits
- allowed input/output roots

Recommended environment variable names:

```text
DT_ENERGYPLUS_EXE
DT_ENERGYPLUS_VERSION
DT_ENERGYPLUS_WEATHER_ROOT
DT_RUN_ROOT
DT_OUTPUT_ROOT
DT_ENERGYPLUS_MODE
```

Policy:

- Real executable paths are local-only.
- Weather library paths are local-only unless pointing to approved public examples.
- Example config should use placeholders, not `C:/Users/...`.
- Current `C:/temp` and `C:/tmp` behavior in agent tools is transitional and should be replaced by
  approved config/backend policy later.
- EnergyPlus execution config should be validated before real subprocess execution is enabled.
- Local install, container, and external service modes should be represented deliberately.

## 8. Backend Configuration Policy

Future backend config may include:

- service host/port defaults
- worker concurrency
- queue settings
- job request defaults
- run/output roots
- API enablement flags
- log level/format
- feature flags
- EnergyPlus execution mode
- timeout/resource limits

Policy:

- Backend config examples may live in root `config/backend/`.
- Backend-internal config, loaders, and service defaults may live in `backend/config/`.
- Credentials stay local-only and should be read from environment variables or secret managers.
- Backend config should validate against schemas once schema policy is implemented.
- Backend should not read random app `.kit` or extension manifests as general runtime config.

## 9. Kit Configuration Boundary

Kit configuration remains where Kit expects it:

- `source/apps/*.kit` for app composition and app settings.
- `source/extensions/*/config/extension.toml` for extension manifests.
- `repo.toml` and `repo_tools.toml` for repo tooling.
- `premake5.lua` and extension-local Premake files for build/prebuild behavior.

Root `config/` may eventually define project-level runtime/backend examples, but it must not
override or shadow Kit's native configuration model.

Generated blocks inside `.kit` files should not be edited casually. App/extension config changes
require build/launch validation when they affect runtime behavior.

## 10. VS Code and Developer Config Boundary

`.vscode/tasks.json`, `.vscode/launch.json`, and `.vscode/settings.json` are developer tooling
configuration.

Policy:

- Do not move IDE settings into root `config/`.
- Shared `.vscode` settings must not expose private paths or secrets.
- `.vscode/settings.json` may contain generated `_build` analysis paths; those are developer
  convenience settings, not project runtime config.
- Local IDE/user settings should remain local-only if they include private paths or credentials.

## 11. Config Schema and Validation Policy

Future config validation should align with `schemas/`:

- Config schemas belong in future `schemas/`.
- Config examples should validate against schemas.
- Config loading and validation code belongs in packages/backend, not in raw config files.
- Validation scripts belong in future `scripts/validation/` or tests.
- Config documentation belongs in `config/README.md` or `docs/development`.
- Generated validation reports should not be committed unless explicitly promoted.

## 12. Naming and File Format Policy

Recommended formats:

| Use | Preferred format | Notes |
| --- | --- | --- |
| Human-edited project config | TOML | Matches existing Kit/repo ecosystem |
| Backend job request examples | JSON or TOML | JSON if API-facing, TOML if manually edited |
| Machine-generated config | JSON | Stable parser support and schema validation |
| Environment variables | `.env.example` | Placeholders only; real `.env` ignored |
| Schema validation config | JSON or TOML | Match validator ecosystem |
| IDE config | JSON under `.vscode/` | Do not move to root `config/` |
| INI | Avoid unless external tool requires it | Use only when tool-native |
| YAML | Avoid by default | Only if a selected tool/framework requires it |

Naming rules:

- lowercase snake_case filenames
- explicit domain names
- no vague names such as `settings.toml` without context
- suffix examples with `.example.toml`, `.example.json`, or use `examples/`
- local-only files should include `.local` or live under ignored local config paths

## 13. Privacy and Security Policy

Forbidden in committed config:

- secrets
- API keys
- tokens
- passwords
- LLM provider keys
- MQTT credentials
- private broker URLs
- real customer/building endpoints
- personal usernames
- user profile paths
- private network shares
- local absolute paths except generic placeholders in documentation
- real EnergyPlus install paths
- real weather/data directories

Sanitization rules:

- Replace real paths with placeholders such as `<path-to-energyplus.exe>`.
- Replace endpoints with `localhost` examples only when clearly illustrative.
- Replace credentials with empty strings or `<set-in-local-env>`.
- Review generated logs before copying into docs/config.

## 14. Codex Access Policy

Codex may inspect config files.

Codex must not:

- create `config/` unless a ticket explicitly allows it.
- create `.env` with real values.
- commit secrets.
- hardcode local absolute paths.
- edit Kit configs unless a ticket explicitly targets Kit config.
- edit `.gitignore` unless a ticket explicitly targets ignore policy.
- promote local config to committed examples without review.

Codex should:

- create example configs only when explicitly requested.
- use placeholders for local paths/secrets.
- validate config examples when possible.
- report config files inspected and changed.
- call out any secret/local-path risk found during inspection.

## 15. Current Artifact Classification

| Artifact | Classification | Recommendation |
| --- | --- | --- |
| `repo.toml` | Kit workflow config | Stay root; edit only under scoped Kit/build/config tickets |
| `repo_tools.toml` | Kit repo tool config | Stay root; high-impact tooling config |
| `premake5.lua` | Kit/Premake build config | Stay root; not root `config/` |
| `source/apps/my_own_software.kit` | Active Kit app config/source | Stay under `source/apps`; not root `config/` |
| `source/extensions/*/config/extension.toml` | Extension manifests | Stay extension-local |
| `.vscode/launch.json` | Developer debug config | Stay `.vscode`; review local/private details if edited |
| `.vscode/tasks.json` | Developer task config | Stay `.vscode`; wraps repo tooling |
| `.vscode/settings.json` | Developer/editor config | Stay `.vscode`; generated `_build` paths are developer convenience |
| `tools/deps/pip.toml` | Kit/tool dependency config | Stay under `tools/deps` |
| `tools/deps/user.toml` | Empty tool dependency/user config | Stay under `tools/deps`; do not add secrets |
| `source/rendered_template_metadata.json` | Generated/template metadata | Do not commit without explicit decision |
| `_build/**/*.toml/json/kit` | Generated config artifacts | Ignored/generated; do not edit or commit |
| `C:/temp`, `C:/tmp` allowed roots | Transitional source behavior | Replace later with backend/config policy |
| `NVIDIA_API_KEY` lookup | Local-only credential convention | Document in future `.env.example`; never commit real key |
| future `.env.example` | Public-safe placeholder config | Future root config candidate |
| future `.env` | Local-only secrets/config | Must be ignored; do not commit |
| future backend config | Backend/project config | Root examples/defaults plus backend-local implementation |
| future EnergyPlus config | Local execution config | Root examples/defaults; real paths local-only |

## 16. Open Decisions

- Whether root `config/` is needed before backend exists.
- Whether TOML should be the default for all human-edited project config.
- Whether to add `.env.example` before real backend/EnergyPlus execution exists.
- Where local-only config should live: root `.env`, `config/local/`, user profile, or app data.
- How EnergyPlus executable discovery should work.
- Whether backend config lives primarily under root `config/backend/` or `backend/config/`.
- When config schemas should be introduced under `schemas/`.
- Whether `.vscode/settings.json` should remain tracked given generated `_build` analysis paths.
- How to handle current `C:/temp`/`C:/tmp` behavior without breaking MVP tools.

## 17. Risks

- Root `config/` can duplicate Kit app or extension config if boundaries are weak.
- Public repo config can leak secrets, local paths, API keys, or private endpoints.
- Introducing config before backend exists can freeze premature assumptions.
- EnergyPlus execution can become unsafe if executable/input/output paths are not validated.
- `.env.example` can drift from real required environment variables.
- `.vscode/settings.json` can accumulate generated/local paths and confuse ownership.
- Local config and generated runtime manifests can be accidentally committed without ignore policy.
- Schema validation can lag behind config examples, causing drift.

## 18. Validation Commands Used for This Contract

Read-only commands used while preparing this document:

```powershell
git status --short
Test-Path config
Test-Path .env
Test-Path .env.example
Get-ChildItem -Recurse -File -Force | Where-Object { $_.Extension -match "\.(toml|json|yaml|yml|ini|env|kit|lua)$" -or $_.Name -match "^\.env" } | Select-Object FullName,Length
rg -n "config|configuration|settings|\.env|ENERGYPLUS|EnergyPlus|C:/temp|C:\\temp|C:/tmp|C:\\tmp|api_key|token|secret|password|mqtt|provider|host|port|output_root|run_root" docs source tools .vscode README.md repo.toml repo_tools.toml premake5.lua
Get-ChildItem source\extensions -Recurse -Filter extension.toml -Force | Select-Object FullName,Length
Get-ChildItem .vscode -Force | Select-Object FullName,Mode,Length
Get-Content repo.toml | Select-Object -First 320
Get-Content repo_tools.toml
Get-Content .vscode\launch.json
Get-Content .vscode\tasks.json
Get-Content source\apps\my_own_software.kit | Select-Object -First 340
Get-Content tools\deps\pip.toml
Get-Content tools\deps\user.toml
Get-Content source\extensions\dt.energy.agent\config\extension.toml
Get-Content source\extensions\custom.aec.modeling\config\extension.toml
Get-Content source\extensions\custom.aec.thermal_viz\config\extension.toml
Get-Content source\extensions\dt.energy.agent\dt\energy\agent\core\safety.py
Get-Content source\extensions\dt.energy.agent\dt\energy\agent\tools\dxf_tools.py | Select-Object -Skip 400 -First 80
Get-Content source\extensions\dt.energy.agent\dt\energy\agent\llm\nvidia_nim_provider.py
Get-Content .vscode\settings.json | Select-Object -First 160
```

## 19. Recommended Next Ticket

Recommended next ticket: close F1.1 with a top-level repository structure index that links all
folder contracts and summarizes source, generated, runtime, vendor, docs, config, and tooling
ownership in one canonical map.
