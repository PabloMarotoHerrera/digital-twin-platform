# Tests Repository Structure Contract

Status: proposed architecture contract  
Scope: future root `tests/` structure only  
Date: 2026-05-24  

## 1. Purpose

This document defines the intended future root-level `tests/` structure for global smoke tests,
integration tests, repository validation tests, fixtures, snapshots, visual checks, performance
checks, and cross-layer validation.

This is a design contract only. It does not create `tests/`, move tests, edit source, run tests,
run build, launch Kit, stage, commit, or push.

The current repository is an NVIDIA Omniverse Kit App Template derivative. The current validated
baseline builds and launches through Kit tooling. Testing policy must respect Kit App Template
workflows and generated test scripts while creating room for future package, backend, and repository
hygiene tests.

## 2. Current Test State Observed

There is currently no root-level `tests/` directory.

Current extension-local test directories:

```text
source/extensions/custom.aec.sketch/custom/aec/sketch/tests/
source/extensions/my_company.my_usd_composer_setup_extension/my_company/my_usd_composer_setup_extension/tests/
```

Current extension-local test files:

```text
source/extensions/custom.aec.sketch/custom/aec/sketch/tests/test_hello.py
source/extensions/custom.aec.sketch/custom/aec/sketch/tests/test_benchmarks.py
source/extensions/my_company.my_usd_composer_setup_extension/my_company/my_usd_composer_setup_extension/tests/test_app_extensions.py
source/extensions/my_company.my_usd_composer_setup_extension/my_company/my_usd_composer_setup_extension/tests/test_app_startup.py
```

Observed test technology:

- Existing extension tests use `omni.kit.test`.
- `custom.aec.sketch` tests are template-like examples, including a public function sample and
  benchmark examples.
- setup extension tests validate enabled extension load status and app startup warning/startup timing.
- Clean-clone validation observed generated scripts under `_build/windows-x86_64/release/`, including
  `tests-custom.aec.modeling.bat` and `tests-dt.energy.agent.bat`.
- Generated `_build/.../tests-*.bat` scripts are build artifacts and must not be committed.
- Kit App Template documentation says `repo.bat test` is the official test entrypoint after build.

## 3. Role of Future Root `tests/`

Future root `tests/` should contain tests that validate repository-level or cross-layer behavior.
It should not replace extension-local, package-local, or backend-local tests.

Root `tests/` should be used for:

- repository hygiene checks
- global smoke test wrappers
- cross-layer integration tests
- clean-clone reproducibility checks
- Kit app launch/load validation wrappers
- backend/Kit integration smoke checks after backend exists
- shared fixtures used by global tests
- approved snapshots
- visual and performance test harnesses when they span more than one component

Root `tests/` should not become a dumping ground for every unit test. Unit tests should stay near the
code they validate.

## 4. What Does Not Belong in Root `tests/`

Do not place these in root `tests/`:

- generated build outputs
- `_build/.../tests-*.bat`
- extension startup classes
- extension manifests
- app `.kit` descriptors
- package implementation code
- backend service implementation code
- large datasets
- real private building data
- EnergyPlus bulk outputs
- trained models or checkpoints
- notebooks
- vendor binaries
- secrets
- local machine config
- temporary debugging scripts
- pycache or bytecode

## 5. Difference From Other Test Locations

### 5.1 Root `tests/` vs extension-local tests

Extension-local tests live with Kit extensions and validate extension behavior through Kit's extension
test system.

Use extension-local tests for:

- `omni.kit.test` tests
- extension startup tests
- extension API tests that require Kit runtime
- extension UI smoke checks, when supported
- extension-specific fixtures
- template tests that are still owned by the extension

Use root `tests/` for:

- checking all required extensions load together
- app-level smoke wrappers
- cross-extension workflows
- repo hygiene checks
- clean-clone smoke automation

### 5.2 Root `tests/` vs package-local tests

Future package-local tests should live under:

```text
packages/<package>/tests/
```

Use package-local tests for:

- pure Python unit tests
- public API tests
- characterization tests before extraction
- algorithm tests
- parser/validator tests
- tests that should run outside Kit

Root `tests/` may contain cross-package tests only when behavior depends on multiple packages.

### 5.3 Root `tests/` vs backend tests

Future backend tests should live under:

```text
backend/tests/
```

Use backend tests for:

- backend orchestration unit tests
- fake EnergyPlus executable tests
- subprocess safety tests
- config validation tests
- backend API tests
- slow/integration tests that require EnergyPlus, when explicitly marked

Root `tests/` may contain backend/Kit integration smoke tests after both layers exist.

### 5.4 Root `tests/` vs validation reports

`docs/validation/` or architecture validation reports are evidence. They describe what was run, when,
against which commit, and what happened.

Root `tests/` contains executable checks. A test may generate evidence, but the long-term validation
report belongs in docs, not in test code.

## 6. Proposed Future Root Layout

Recommended future layout:

```text
tests/
  smoke/
  integration/
  repo_hygiene/
  kit/
  backend/
  fixtures/
  snapshots/
  visual/
  performance/
```

Create these folders only when real tests are added. This ticket does not create them.

## 7. Test Category Policy

### 7.1 `tests/smoke/`

Purpose: fast, high-signal checks that the repository baseline still works.

Examples:

- clean clone command plan
- build smoke wrapper
- app launch smoke wrapper
- extension load smoke check
- no-window/headless launch smoke if supported

Ownership: repository-level.

Default execution: manual or explicitly requested until automation is stable.

### 7.2 `tests/integration/`

Purpose: cross-layer tests that require multiple components.

Examples:

- Kit extension plus package API integration
- Kit adapter plus backend client integration
- AEC model export through package contract
- EnergyPlus backend result imported into Kit visualization

Ownership: repository-level, with component owners involved.

Default execution: not by default if slow, GPU-bound, or externally dependent.

### 7.3 `tests/repo_hygiene/`

Purpose: validate repository hygiene and Git policy.

Checks should include:

- no tracked `_build/`
- no tracked `_repo/`
- no tracked `_compiler/`
- no tracked `__pycache__/`
- no tracked `.pyc`
- no generated tree dumps committed
- `source/apps` is not ignored
- `source/extensions` is not ignored
- no forbidden large artifacts
- no local AppData paths
- no obvious secrets
- no committed runtime logs

Ownership: repository architecture/hygiene.

Default execution: safe to run often once implemented.

### 7.4 `tests/kit/`

Purpose: global Kit app tests that are not owned by one extension.

Examples:

- app descriptor exists
- generated app launch script exists after build
- all required local extensions load
- app reaches ready state
- RTX readiness check if relevant
- generated extension test script discovery

Ownership: Kit integration layer.

Default execution: manual or smoke workflow; may require Windows/GPU/Kit runtime.

### 7.5 `tests/backend/`

Purpose: repository-level backend integration tests, not backend unit tests.

Examples:

- Kit-to-backend smoke after backend exists
- backend job manifest compatibility with package contracts
- fake backend service called from a Kit adapter

Ownership: cross-layer.

Default execution: not by default until backend exists.

### 7.6 `tests/fixtures/`

Purpose: small shared fixtures used by root tests.

Allowed fixture types:

- tiny USD files
- small telemetry CSV/JSON files
- tiny IDF snippets
- fake EnergyPlus executable scripts for tests
- small expected text outputs

Forbidden fixture types:

- private building models
- large simulation outputs
- large EPW libraries
- trained models
- proprietary vendor files without approval

### 7.7 `tests/snapshots/`

Purpose: approved expected output snapshots.

Preferred snapshot types:

- text snapshots
- JSON snapshots
- schema snapshots
- small IDF expected output snapshots

Visual snapshots are allowed only with explicit approval because viewport rendering can be brittle
across GPU, driver, Kit, and display settings.

### 7.8 `tests/visual/`

Purpose: visual smoke or visual regression checks.

Policy:

- visual smoke checks may verify that a viewport/canvas is nonblank or that key UI appears
- full visual regression requires explicit approval
- GPU and RTX dependency must be marked
- screenshots must avoid private project data
- visual tests should not run by default

### 7.9 `tests/performance/`

Purpose: benchmarks and performance checks that span the app or repository.

Policy:

- performance tests should not run by default
- benchmarks must record hardware/environment
- thresholds should be conservative and reviewed
- extension-local benchmark templates should stay extension-local until real benchmarks exist

## 8. Extension-Local Test Policy

Extension-local tests should remain inside the owning extension when they require Kit extension
runtime, `omni.kit.test`, extension enablement, extension-private APIs, or extension-local fixtures.

Current extension-local tests should remain where they are for now:

- `custom.aec.sketch` template tests
- `my_company.my_usd_composer_setup_extension` startup/load tests

Template-generated tests should be classified before relying on them:

- template examples are not proof of product behavior
- keep them if they still validate extension health
- replace or supplement them with real product tests over time
- do not move them to root solely for organization

Generated `tests-*.bat` scripts:

- are generated by Kit tooling under `_build`
- are runtime/build artifacts
- should remain ignored
- may be invoked manually or by future smoke workflows
- should not be edited or committed

Move or duplicate a test into root `tests/` only when:

- it validates cross-extension behavior
- it validates app-level behavior
- it is independent of extension-private implementation
- it is part of repository smoke or hygiene validation

## 9. Package-Local Test Policy

Future packages should use package-local tests:

```text
packages/<pkg>/tests/
```

Policy:

- tests should run outside Kit when possible
- pure logic should be tested with normal Python test tools
- public APIs should have direct tests
- extraction candidates should get characterization tests before moving
- package tests should not import from `source/extensions`
- package tests should avoid GPU, Kit, and external executables unless explicitly marked
- pytest is a likely candidate, but the final test framework remains an open decision

Examples:

- `dt_geometry` polygon/mesh algorithm tests
- `dt_sensors` telemetry series and CSV/JSON parser tests
- `dt_energyplus` IDF builder tests
- `dt_ai` tool schema/message tests

## 10. Backend Test Policy

Future backend tests should live under:

```text
backend/tests/
```

Policy:

- fast tests should run without EnergyPlus
- subprocess wrapper tests should use fake executables
- path safety tests should use temp directories
- integration tests requiring real EnergyPlus must be marked `energyplus`, `integration`, and `slow`
- real runs must write to temp or approved `runs/` locations
- no long simulations in the default test suite
- backend service/API tests should avoid network exposure unless explicitly scoped

Examples:

- config loading tests
- EnergyPlus command construction tests
- fake executable success/failure tests
- timeout/cancellation tests
- run manifest tests
- output parser tests with small fixtures

## 11. Repository Hygiene Tests

Future hygiene checks should be safe, fast, and local.

Recommended checks:

```text
git ls-files _build
git ls-files _repo
git ls-files _compiler
git ls-files | Select-String "__pycache__|\\.pyc$"
git check-ignore -v source/apps/my_own_software.kit
git check-ignore -v source/extensions/dt.energy.agent/config/extension.toml
git check-ignore -v repo_tree.txt
```

Expected policy:

- generated/runtime directories are ignored and untracked
- product source is visible to Git
- generated dumps are ignored
- Python bytecode is ignored
- local developer artifacts are not tracked
- large/unknown owner-decision files are not accidentally staged

Hygiene tests must not delete files. They should report violations only.

## 12. Smoke Test Workflow

Future smoke workflow should be explicit and staged.

Recommended smoke ladder:

1. Clean clone smoke: clone repository to a temp directory.
2. Git state smoke: verify clean status and expected remotes.
3. Source existence smoke: verify app descriptor and key extension manifests exist.
4. Generated artifact absence smoke: verify `_build`, `_repo`, `_compiler`, and forbidden local files are absent from committed baseline.
5. Build smoke: run `repo.bat build`.
6. Generated script smoke: verify expected app/test scripts exist under `_build/windows-x86_64/release/`.
7. App launch smoke: run `repo.bat launch my_own_software.kit`.
8. Readiness smoke: detect `app ready` and `RTX ready` when relevant.
9. Extension load smoke: verify active local extensions loaded.
10. Post-run Git smoke: confirm source remains clean and generated outputs are ignored.

No-window/headless launch should be preferred if Kit supports it for this app, but it must be
validated before becoming policy.

Generated extension test scripts may become part of the smoke workflow after their behavior and
runtime cost are reviewed.

## 13. Fixture Policy

Fixture rules:

- keep fixtures small and deterministic
- commit only license-safe fixtures
- prefer synthetic fixtures over real private building data
- document fixture provenance
- avoid generated bulk outputs
- avoid binary fixtures unless necessary
- use tiny representative samples

EnergyPlus fixtures:

- small IDF snippets may be committed after review
- small EPW/weather snippets require license and usefulness review
- real EnergyPlus output fixtures should be tiny and explicitly approved
- full simulation output folders should not be committed

USD fixtures:

- use tiny synthetic USD scenes
- avoid private building geometry
- keep schemas/conventions clear
- prefer text USDA where practical

Telemetry fixtures:

- small CSV/JSON samples are acceptable
- no real sensor feeds without anonymization and owner approval
- include timestamp/channel conventions

## 14. Snapshot Policy

Snapshots are acceptable when they stabilize a public contract.

Good snapshot candidates:

- IDF text output from a tiny model
- JSON result objects
- tool schema output
- repository hygiene expected output
- small telemetry normalization output

Risky snapshot candidates:

- full Kit logs
- screenshots across GPU/driver versions
- unordered stage traversal output
- large generated files

Rules:

- snapshots must be reviewed intentionally
- update snapshots only when behavior changes intentionally
- visual snapshots need explicit approval
- snapshots should not include machine paths, secrets, or private data

## 15. Visual and Performance Test Policy

Visual tests:

- distinguish visual smoke from visual regression
- visual smoke may check app launch, nonblank viewport, UI presence, or expected extension window
- visual regression should be opt-in and environment-aware
- GPU/RTX dependency must be marked
- do not run visual tests by default

Performance tests:

- benchmark tests should be opt-in
- record hardware, OS, GPU, driver, Kit version, and commit
- avoid strict thresholds until enough baseline data exists
- extension-local benchmark examples should not be treated as product performance coverage

## 16. Markers and Naming Conventions

Suggested future markers:

```text
unit
integration
slow
kit
backend
energyplus
smoke
visual
performance
requires_gpu
repo_hygiene
```

Naming conventions:

- Python tests: `test_<behavior>.py`
- smoke scripts: `smoke_<workflow>.ps1` or `test_<workflow>.py`, depending on chosen framework
- fixtures: descriptive lowercase snake_case
- snapshots: match the test name and expected output type
- generated scripts keep Kit-generated names and stay under `_build`

Markers should be documented before CI or automation depends on them.

## 17. Codex Test Execution Policy

Docs-only changes:

- do not run build, launch, Kit tests, backend tests, or EnergyPlus
- run read-only validation commands only if requested

Package changes:

- run affected package tests
- run Kit smoke validation if package changes affect extensions
- do not run GPU/slow tests unless requested

Extension changes:

- run targeted extension tests if available and allowed
- run `repo.bat build` for app/extension config or source changes that affect Kit packaging
- run app launch or no-window smoke for startup/UI/extension loading changes

Backend changes:

- run fast backend tests
- do not run real EnergyPlus unless explicitly requested
- mark and skip slow/integration tests by default

Repo hygiene changes:

- run git status, git check-ignore, and relevant hygiene checks
- do not cleanup unless the ticket explicitly allows cleanup

Codex must not run:

- long simulations
- real EnergyPlus integration tests
- GPU/visual/performance tests
- generated test scripts with unknown duration

unless the ticket explicitly permits them.

## 18. CI and GitHub Actions Future Policy

No CI is required immediately.

Future CI candidates:

- lightweight repo hygiene checks
- package unit tests after `packages/` exists
- backend fast tests after `backend/` exists
- documentation link/style checks if useful

Kit CI constraints:

- Kit app launch may require Windows, GPU, drivers, and Omniverse runtime dependencies
- GitHub-hosted CI may not be sufficient for full Kit launch
- generated Kit test scripts may need a self-hosted runner
- RTX readiness validation is environment-dependent

Recommended future model:

- GitHub Actions for fast hygiene/package/backend tests
- manual or self-hosted Windows/GPU workflow for Kit build/launch smoke
- validation reports in docs for major baseline changes

## 19. Current Test Candidate Classification

| Candidate | Classification | Recommendation |
| --- | --- | --- |
| `custom.aec.sketch` `test_hello.py` | extension-local/template test | Keep in extension for now; review whether `some_public_function` is real product behavior. |
| `custom.aec.sketch` `test_benchmarks.py` | extension-local/template benchmark | Keep in extension for now; should not run by default as product performance coverage. |
| setup extension `test_app_extensions.py` | extension-local Kit load test | Keep in extension; useful as startup/load validation, but tied to template setup extension. |
| setup extension `test_app_startup.py` | extension-local startup metric test | Keep in extension; review warning-count expectations before making it gating. |
| `_build/windows-x86_64/release/tests-*.bat` | generated test scripts | Do not commit or edit; future smoke workflow may invoke after build. |
| clean-clone validation workflow | future root smoke/integration workflow | Convert into documented smoke script only after explicit automation ticket. |
| future package tests | package-local tests | Put under `packages/<pkg>/tests`; run outside Kit when possible. |
| future backend/EnergyPlus tests | backend tests | Put fast tests under `backend/tests`; mark real EnergyPlus tests slow/integration. |
| future root smoke tests | root `tests/smoke` | Add only after smoke workflow and expected runtime are approved. |
| future repo hygiene tests | root `tests/repo_hygiene` | Good early candidate; safe if read-only. |
| future visual tests | root `tests/visual` or extension-specific | Requires explicit approval and GPU-aware policy. |
| future performance tests | root `tests/performance` or extension-local | Should not run by default. |

## 20. Open Decisions

Open decisions:

1. Whether future pure Python tests should standardize on pytest.
2. How `repo.bat test` should relate to root `tests/` automation.
3. Whether generated `tests-*.bat` scripts should be part of smoke validation.
4. Whether the app supports reliable headless/no-window launch.
5. Whether Kit launch smoke can run in CI or needs self-hosted Windows/GPU.
6. Whether EnergyPlus tests will use local executable, fake executable, container, or remote service.
7. Fixture size limits and exact artifact policy.
8. Visual regression strategy and whether it is worth the maintenance cost.
9. Performance test runtime budget and baseline environment.
10. Public repo policy for any test data derived from real buildings or sensors.
11. Whether current template tests should be kept, rewritten, or retired.

## 21. Risks

- Root `tests/` could duplicate extension/package/backend tests if ownership is not enforced.
- Kit tests may be brittle across Kit versions, GPU drivers, and local Omniverse state.
- Generated `_build` test scripts are useful but not source-of-truth.
- Template tests may give false confidence if not replaced with product behavior tests.
- Visual snapshots can be noisy and expensive to maintain.
- EnergyPlus tests can become slow, platform-dependent, or unsafe without fake-executable coverage.
- Fixtures can leak private building/sensor data if public/private review is skipped.
- CI may fail for environment reasons unrelated to source correctness if Kit launch is automated too early.

## 22. Recommended Future Tickets

Recommended follow-up tickets:

1. Classify existing extension-local tests as template placeholder, useful smoke, or retire.
2. Design a read-only repo hygiene test script before creating root `tests/`.
3. Define a no-window Kit launch smoke command if supported.
4. Add characterization tests for the first package extraction candidate.
5. Define backend fake EnergyPlus executable test strategy before implementing real EnergyPlus runner.
6. Decide pytest and marker policy before creating package/backend tests.
