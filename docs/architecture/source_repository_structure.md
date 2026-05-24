# Source Repository Structure Contract

Date: 2026-05-24

Scope: architecture/design only. This document defines the intended contract for `source/` in the current Omniverse Kit App Template derivative. It does not authorize immediate file moves, renames, package extraction, source rewrites, or build behavior changes.

## 1. Executive Summary

`source/` is the current product source-of-truth for Kit-integrated application source in this repository.

The current committed contract is:

- `source/apps/` owns Kit application descriptors.
- `source/extensions/` owns local Kit extensions.
- `source/apps/my_own_software.kit` is the active app descriptor.
- The active extension set is under `source/extensions/`.

Because this repository remains an NVIDIA Omniverse Kit App Template derivative, `source/apps` and `source/extensions` must remain in place for now. Future moves or package extraction may be useful, but they must be staged as later migrations with clean-clone validation after each step.

`source/` must not become a general dumping ground for generated output, runtime state, simulation output, large vendor assets, notebooks, generic backend services, or long-term reusable non-Kit packages. Its purpose is Kit-integrated source.

## 2. Current Committed `source/` Structure

Current tracked source, verified with `git ls-files source`, contains:

```text
source/
  apps/
    my_own_software.kit
  extensions/
    custom.aec.sketch/
    custom.aec.primitive_mesh/
    custom.aec.extrude/
    custom.aec.modeling/
    custom.aec.thermal_viz/
    dt.energy.agent/
    my_company.my_usd_composer_setup_extension/
```

The local working copy also contains untracked files:

```text
source/rendered_template_metadata.json
source/source_tree.txt
source/apps/my_own_software.kit.before_extension_cleanup
```

Those untracked files are not part of the current committed source contract. They remain owner-decision or generated/temporary artifacts as classified in earlier repository hygiene documents.

## 3. Architectural Role of `source/`

### Source-of-Truth

`source/apps` and `source/extensions` are product source-of-truth. Changes to app composition, local extension behavior, extension metadata, extension UI, bundled extension assets, and Kit-integrated Python modules should be made here, not under `_build/`.

### Kit-Managed and Product-Owned

`source/` is both:

- Kit-expected: Kit App Template tooling expects app and extension source in this area.
- Product-owned: the local app and local extensions are project source, not generated runtime output.

The distinction matters:

- `source/apps/*.kit` and `source/extensions/*` are authored source, even if originally rendered from templates.
- `_build/windows-x86_64/*/exts/*` is generated runtime output copied/linked from `source/extensions`.
- Kit-generated blocks inside `.kit` files require extra care, but the file itself remains app source.

### Template-Derived Areas

Template-derived source currently includes:

- `source/apps/my_own_software.kit`, originally based on `omni.usd_composer`.
- `source/extensions/my_company.my_usd_composer_setup_extension`, still named like a template-derived setup extension.
- Some extension docs/tests/metadata and NVIDIA template headers.

Template-derived does not mean disposable. If a template-derived extension is active in the app, it is source-of-truth until deliberately replaced.

### Generated/Runtime Content That Must Not Enter `source/`

Do not add these under `source/`:

- `_build` outputs or copied runtime extension folders.
- `__pycache__/` and `.pyc`.
- generated tree dumps such as `source_tree.txt`.
- runtime logs.
- local user configuration from AppData or Omniverse user caches.
- one-off backups such as `*.before_extension_cleanup` unless explicitly approved.

## 4. Intended `source/apps/` Structure

### Purpose

`source/apps/` contains Kit app descriptors only. Each app descriptor defines a runnable application composition: package metadata, Kit dependencies, local extension dependencies, settings, app extension folders, and generated Kit version-lock sections.

Current active app:

```text
source/apps/my_own_software.kit
```

### Naming Policy

Current name is accepted as baseline:

```text
my_own_software.kit
```

Future app renaming is allowed only as a migration ticket because it affects:

- `source/apps/*.kit`
- root `premake5.lua` `define_app(...)`
- `repo.toml` precache configuration
- generated launch scripts
- user-level Kit settings paths
- documentation and screenshots

Do not rename in incidental feature tickets.

### Allowed Files

Allowed under `source/apps/`:

- active `.kit` app descriptors.
- optional app-layer `.kit` files if intentionally introduced by Kit workflow.
- app-specific README only if it documents app composition and is intentionally referenced.

### Forbidden Files

Forbidden under `source/apps/` by default:

- backup snapshots such as `*.before_extension_cleanup`.
- generated `.kit` outputs from `_build`.
- launch scripts such as `*.bat` generated under `_build`.
- local user settings or caches.
- build logs.
- app-specific runtime data.

### Generated Blocks Inside `.kit`

`.kit` files may contain generated Kit sections, including version-lock blocks. These sections are allowed inside source app descriptors, but must be treated as generated subregions.

Rules:

- Do not hand-edit generated blocks unless the ticket is explicitly about Kit dependency/version-lock management.
- Prefer official repo/Kit tooling when regenerating dependency lock sections.
- If a generated block changes, validate with `repo.bat build` and app launch or a no-window smoke test.

### Relationship With `repo.toml` and `premake5.lua`

Every active app descriptor under `source/apps/` must be wired deliberately:

- root `premake5.lua` must define the app with `define_app("...")`.
- `repo.toml` precache/build tooling should reference the app when extension precaching depends on it.
- `repo.bat launch --help` should list the app.
- clean clone validation should confirm the app builds and launches.

App descriptor changes must be reviewed together with these root Kit integration files.

## 5. Intended `source/extensions/` Structure

### Purpose

`source/extensions/` contains local Kit extensions that are either directly loaded by the app or are declared dependencies of loaded local extensions.

Current active extension set:

```text
custom.aec.sketch
custom.aec.primitive_mesh
custom.aec.extrude
custom.aec.modeling
custom.aec.thermal_viz
dt.energy.agent
my_company.my_usd_composer_setup_extension
```

### Extension Folder Naming

Extension folder names should match Kit extension names. Current patterns:

- `custom.aec.*` for AEC product extensions.
- `dt.energy.agent` for the digital twin agent extension.
- `my_company.my_usd_composer_setup_extension` for template-derived setup glue.

Future extensions should use stable, domain-oriented names. Avoid throwaway names such as `try.one`, `test.extension`, or user initials in committed source.

### Standard Extension Layout

Preferred extension layout:

```text
source/extensions/<extension.name>/
  config/
    extension.toml
  <python package root>/
    ...
  data/                 optional runtime assets
  docs/                 optional extension-local docs
  tests/                optional extension-local tests, often under package root
  .gitignore            optional local cache guard
  premake5.lua
  README.md             optional extension overview
```

Not every extension needs every optional folder. The required minimum for a Python Kit extension is normally:

- `config/extension.toml`
- Python module package declared in `extension.toml`
- `premake5.lua` that links the package/config/assets correctly

### `config/extension.toml` Ownership

`config/extension.toml` is the public Kit metadata and dependency contract for each extension.

It owns:

- package title/version/category/description.
- Kit extension dependencies.
- local extension dependencies.
- Python module registration.
- documentation/test metadata where applicable.

Rules:

- If an extension imports another extension's Python package, it must also declare the corresponding extension dependency in `extension.toml`.
- Do not rely on hidden app load order for import availability.
- Optional dependencies must be marked optional only when the extension can actually run without them.
- Repository URLs inherited from templates should be corrected in a future metadata cleanup ticket, not casually.

### Python Package Layout

Current package layout is mixed:

- `custom.aec.sketch` uses package path `custom/aec/sketch`.
- Most AEC extensions use namespace package root `custom_aec/...`.
- `dt.energy.agent` uses `dt/energy/agent`.
- setup extension uses `my_company/my_usd_composer_setup_extension`.

Current mixed layout is accepted for baseline reproducibility. Future namespace standardization is an open decision.

Rules:

- Python package roots must match `[[python.module]]` in `extension.toml`.
- Shared namespace packages such as `custom_aec` require care because multiple extensions contribute to the same namespace.
- Cross-extension imports must go through declared extension dependencies.
- Avoid importing private implementation modules across extension boundaries unless no public API exists yet.

### `data/` Assets Policy

`data/` under an extension is for small-to-moderate runtime assets needed by that extension:

- icons and preview images.
- bundled sample data that supports demos/tests.
- layout/stage template assets when the extension owns them.
- USD/USDA/MDL assets required by the extension.

Current examples:

- `custom.aec.sketch/data/icon.png`
- `custom.aec.sketch/data/preview.png`
- `custom.aec.thermal_viz/data/sample_temperature_day.csv`
- setup extension material and icon assets.

Do not put large datasets, simulation outputs, downloaded vendor runtimes, EnergyPlus installs, or trained models in extension `data/` without an explicit artifact policy.

### Extension Docs Policy

Extension-local docs are allowed when they explain extension-specific behavior, Extension Manager metadata, or local usage.

Use repository-level `docs/architecture` for cross-extension architecture contracts.

Avoid duplicating architecture policy inside extension-local docs. If extension docs drift from architecture docs, the architecture docs define the repository contract and extension docs should be updated later.

### Extension Tests Policy

Tests inside active extension folders are allowed and should be tracked if they are part of the Kit extension baseline.

Current tests include template-derived tests in:

- `custom.aec.sketch/custom/aec/sketch/tests`
- `my_company.my_usd_composer_setup_extension/.../tests`

Rules:

- Keep template-derived tests for baseline continuity until replaced.
- Mark weak/template tests for later review instead of deleting them opportunistically.
- Future tests should distinguish smoke tests, extension startup tests, domain logic tests, and integration tests.
- Headless/domain logic tests are candidates for future `packages/` extraction if they should run outside Kit.

### Extension-Local `.gitignore` Policy

Extension-local `.gitignore` files are allowed for local cache guards only. Current pattern:

```text
__pycache__/
*.pyc
```

Do not use extension-local `.gitignore` to hide source files, generated source snapshots, large local assets, or owner-decision files. Repository-level `.gitignore` should handle common generated artifacts.

### Per-Extension `premake5.lua` Policy

Each extension's `premake5.lua` is part of the Kit build/prebuild source contract. It should:

- call `get_current_extension_info()`.
- call `project_ext(ext)`.
- link only the source folders/assets that belong in runtime extension output.

Do not add unrelated filesystem operations or cleanup behavior to extension `premake5.lua`. If an extension adds assets, update `premake5.lua` deliberately and validate generated `_build/.../exts/<extension>` output.

## 6. Current Extension Role Classification

| Extension | Current role | Architectural category | Future candidate role |
| --- | --- | --- | --- |
| `custom.aec.sketch` | Interactive sketch/curve authoring using Kit curve tools | interactive authoring | May remain a UI authoring extension; sketch domain helpers may later move to reusable packages |
| `custom.aec.primitive_mesh` | Parametric primitive mesh creation | geometry implementation | future package extraction candidate for mesh generation logic if made Kit-independent |
| `custom.aec.extrude` | Closed sketch/curve extrusion into mesh/block geometry | geometry implementation | future package extraction candidate for geometry algorithms |
| `custom.aec.modeling` | Unified AEC modeling UI/API, rebuilds, spaces/surfaces, metadata, thermal readiness | semantic AEC modeling | future service boundary and package extraction candidate; should become the public AEC domain API |
| `custom.aec.thermal_viz` | Thermal/telemetry UI, viewport rendering, CSV/JSON/MQTT ingestion | visualization / telemetry | future service boundary candidate for telemetry adapters; visualization should depend on documented AEC conventions |
| `dt.energy.agent` | Chat/agent UI, rule-based intent parsing, tool registry, AEC/IDF/DXF tooling facade | AI orchestration / agent tools | future package or service extraction candidate for core/tools if they become headless/testable |
| `my_company.my_usd_composer_setup_extension` | USD Composer setup glue, app defaults, layouts, stage template, menu/title behavior | app setup / template glue | future rename/replacement candidate once app identity stabilizes |

## 7. What Must Not Live Under `source/`

Do not place these under `source/`:

- `_build`, `_repo`, `_compiler`, or any generated Kit runtime output.
- generated launch scripts or copied runtime extensions.
- `__pycache__/`, `.pyc`, `.pyo`, `.pyd`.
- generated tree dumps such as `source_tree.txt`.
- backup `.kit` files or snapshot files unless explicitly approved.
- local AppData/user paths or user preference exports.
- logs, cache files, crash dumps, telemetry dumps.
- EnergyPlus simulation runs, IDF output folders, EPW copies, SQLite results, or report files.
- large external binaries or vendor runtimes.
- large datasets or research corpora.
- trained models or model checkpoints.
- research notebooks.
- generic backend code intended to run independently of Kit.
- reusable domain libraries that should be imported by tests/services outside Kit.
- secrets, API keys, tokens, local credentials, or `.env` files.

If a file is useful but not Kit-integrated source, classify it before adding it. Likely destinations are future `packages/`, `backend/`, `data/`, `vendor/`, `experiments/`, or external artifact storage.

## 8. Future `source/` Evolution Policy

### Keep `source/` Kit-Integrated

For the current phase, `source/` should remain limited to Kit app descriptors and Kit extensions.

Recommended future top-level boundaries:

- reusable Python/domain packages: `packages/`
- headless services/backend: `backend/`
- experiments/research notebooks: `experiments/` or separate research repo
- test fixtures and small canonical data: `tests/fixtures/` or extension-specific `data/`
- large data/vendor binaries: artifact store, Git LFS, or dedicated `vendor/` only after policy approval

These folders are future design candidates, not approved immediate migrations.

### Migration Staging Rules

Future migration sequence:

1. Document the boundary and target folder.
2. Add tests or smoke checks around the behavior.
3. Extract one boundary at a time.
4. Preserve extension public behavior.
5. Update `extension.toml` dependencies and imports deliberately.
6. Run `repo.bat build`.
7. Run app launch or no-window smoke validation.
8. Update architecture docs after validation.

Do not combine package extraction, app renaming, extension renaming, and Kit dependency updates in one ticket.

## 9. Dependency Direction Rules Within `source/`

### App Direction

`source/apps/my_own_software.kit` may depend on local extensions and external Kit extensions. It should compose capabilities but not contain domain implementation logic.

### Extension Direction

Extensions may depend on:

- Kit extensions declared in `config/extension.toml`.
- local extensions declared in `config/extension.toml`.
- their own package modules.

Extensions must not depend on hidden Python imports without declaring extension dependencies.

Current acceptable dependencies:

- `custom.aec.modeling` declares `custom.aec.extrude` and `custom.aec.primitive_mesh`.
- `dt.energy.agent` declares `custom.aec.modeling`, `custom.aec.primitive_mesh`, and `custom.aec.extrude`.

Current risk:

- `custom.aec.thermal_viz` relies on AEC spaces/metadata conventions but does not declare dependency on `custom.aec.modeling`. If this reliance becomes direct rather than convention-based, add an explicit dependency or formal shared convention package.

### Public API Rule

Cross-extension calls should prefer public APIs or tool interfaces.

Examples:

- Agent tools should call `custom_aec.modeling.api` or stable tool APIs, not private UI internals.
- Visualization should consume documented AEC attributes/hierarchy, not arbitrary private structures.
- Geometry implementation extensions should expose narrow functions used by modeling, not broad UI state.

### UI vs Domain Logic Rule

UI extensions may temporarily own domain logic in the MVP phase, but long-term reusable logic should move toward headless modules or packages.

Potential extraction candidates:

- AEC rebuild and geometry logic from `custom.aec.modeling`.
- mesh generation from `custom.aec.primitive_mesh`.
- extrusion algorithms from `custom.aec.extrude`.
- agent tool registry/core logic from `dt.energy.agent`.
- telemetry adapters from `custom.aec.thermal_viz`.

These are future package extraction candidates only.

## 10. Source Hygiene Rules

Required hygiene for `source/`:

- no `__pycache__/`.
- no `.pyc`, `.pyo`, `.pyd`.
- no generated tree dumps.
- no local backup snapshots unless approved.
- no runtime logs or generated app data.
- no `_build` copies.
- no local AppData, user profile, or absolute user paths.
- no hardcoded local absolute paths except temporary MVP placeholders clearly marked and reviewed.
- no secrets or tokens.
- no simulation result output.
- no unreviewed large binary assets.

Allowed assets must be intentionally bundled with an extension and referenced by that extension.

## 11. Codex Interaction Policy for `source/`

### Codex May Edit

Codex may edit:

- `source/apps/*.kit` only when the task is app composition/configuration and validation is planned.
- `source/extensions/*/config/extension.toml` only when changing extension dependencies, metadata, tests, or module registration.
- extension Python source when implementing requested behavior.
- extension docs/tests/assets when relevant to the task.
- extension `premake5.lua` when adding/removing linked runtime folders.

### Codex May Inspect Only

Codex should inspect but avoid incidental edits to:

- generated blocks inside `.kit` files.
- template-derived setup extension internals unless the task targets app setup.
- bundled MDL/USD/template assets unless the task targets assets.
- extension tests that are known template placeholders unless the task targets tests.

### Codex Must Not Edit

Codex must not edit:

- `_build` runtime copies instead of `source`.
- `__pycache__` or `.pyc` except as part of an explicit cleanup ticket.
- untracked backup/snapshot files as a substitute for source changes.
- user-level Kit/AppData files as part of repository changes.
- generated Kit version-lock blocks unless explicitly requested.

### Validation Expectations

Run validation when changes affect:

- app descriptor dependencies/settings.
- extension dependencies or module names.
- `premake5.lua` link behavior.
- cross-extension imports.
- startup behavior.
- USD hierarchy conventions.
- setup extension behavior.

Preferred validation levels:

- metadata/source-only changes: inspect and possibly `git diff`.
- extension dependency changes: `repo.bat build`.
- app startup or UI extension changes: `repo.bat build` plus app launch/no-window smoke test.
- reusable logic extraction: unit tests plus Kit smoke validation.

Do not run build/launch for documentation-only source structure tickets unless explicitly requested.

## 12. Open Decisions

| Decision | Current state | Risk if deferred | Future direction |
| --- | --- | --- | --- |
| Keep or rename `my_own_software.kit` | Current active app name | Generic name leaks into launch scripts/user config | Future app naming ticket after baseline stabilizes |
| Keep or rename `my_company.my_usd_composer_setup_extension` | Active setup extension with template-derived name | Template identity leaks into product architecture | Future setup extension identity migration |
| Standardize `custom_aec` vs `custom.aec` Python namespace | Mixed package layout | Import confusion and namespace package complexity | Future namespace policy/migration |
| Extract `custom.aec.modeling` domain logic | Currently UI/API mixed | UI extension can become too large and hard to test | Future `packages/` extraction after tests exist |
| Extract primitive/extrude algorithms | Currently Kit extension modules | Geometry logic remains tied to Kit runtime | Future headless package if algorithms need independent tests |
| Extract `dt.energy.agent` core/tools | Currently inside Kit extension | Agent logic tied to UI/runtime, harder to service-test | Future package/service boundary |
| Clarify `custom.aec.thermal_viz` dependency on modeling | Convention dependency only | Hidden coupling to AEC hierarchy/attributes | Document AEC conventions or declare dependency if direct import emerges |
| Extension-local tests quality | Some template-derived tests | Weak test signal | Future test audit/rewrite |
| Correct template repository URLs in extension metadata | Some still point to NVIDIA template repo | Misleading ownership metadata | Future metadata cleanup |

## 13. Risks

- Moving `source/apps` or `source/extensions` would break Kit template assumptions unless root tooling is updated and validated.
- Renaming app/extension IDs affects generated launch scripts, user settings, extension dependencies, and docs.
- Hidden Python imports across extensions can pass locally but fail under different load order.
- Generated `.kit` blocks may be overwritten by Kit tooling if edited manually.
- Template-derived setup extension is active; treating it as disposable would break app startup/defaults.
- Current untracked `source/rendered_template_metadata.json` and backup app descriptor can confuse source ownership if accidentally staged later.
- Pycache pollution exists physically in the local working copy even though ignored; cleanup should be a separate ticket.

## 14. Contract Summary

For the current architecture phase:

```text
source/
  apps/        Kit app descriptors only; product source-of-truth.
  extensions/  Local Kit extensions only; product source-of-truth.
```

`source/` is not for generated/runtime state, research, vendor payloads, general backend services, or long-term reusable non-Kit packages.

No immediate migrations are approved by this document. Future changes to structure must preserve clean-clone reproducibility and validate the Kit workflow.
