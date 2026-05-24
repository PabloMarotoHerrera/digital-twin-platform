# Packages Repository Structure Contract

Status: proposed architecture contract  
Scope: future `packages/` structure only  
Date: 2026-05-24  

## 1. Purpose

This document defines the intended future `packages/` structure for reusable, headless, testable
Python libraries in the digital twin platform repository.

This is a design contract only. It does not create `packages/`, extract code, move files, edit Kit
configuration, or change build/launch behavior.

The current reproducible baseline remains an NVIDIA Omniverse Kit App Template derivative. The
current Kit-integrated product source-of-truth remains:

```text
source/apps/
source/extensions/
```

Future `packages/` code should be introduced only after explicit extraction tickets.

## 2. Current State Observed

There is currently no `packages/` directory and no product-level Python package metadata such as
`pyproject.toml`, `setup.cfg`, or `setup.py` outside template scaffolding.

Current extension folders inspected:

```text
source/extensions/custom.aec.primitive_mesh/
source/extensions/custom.aec.extrude/
source/extensions/custom.aec.modeling/
source/extensions/custom.aec.thermal_viz/
source/extensions/dt.energy.agent/
```

Important current modules:

```text
custom.aec.primitive_mesh/custom_aec/primitive_mesh/mesh_builder.py
custom.aec.extrude/custom_aec/extrude/mesh_builder.py
custom.aec.modeling/custom_aec/modeling/api.py
custom.aec.modeling/custom_aec/modeling/rebuild.py
custom.aec.modeling/custom_aec/modeling/rebuild_polygon.py
custom.aec.modeling/custom_aec/modeling/opening_specs.py
custom.aec.modeling/custom_aec/modeling/partition_specs.py
custom.aec.thermal_viz/custom_aec/thermal_viz/timeseries.py
custom.aec.thermal_viz/custom_aec/thermal_viz/data_sources.py
custom.aec.thermal_viz/custom_aec/thermal_viz/mqtt_client.py
custom.aec.thermal_viz/custom_aec/thermal_viz/model_access.py
custom.aec.thermal_viz/custom_aec/thermal_viz/viewport_renderer.py
dt.energy.agent/dt/energy/agent/core/
dt.energy.agent/dt/energy/agent/llm/
dt.energy.agent/dt/energy/agent/tools/
dt.energy.agent/dt/energy/agent/ui/
```

Observed coupling:

- Many geometry and AEC modules currently depend directly on `pxr`, `omni.usd`, `carb`, or Kit UI.
- `custom.aec.modeling` imports mesh builders from `custom_aec.primitive_mesh` and
  `custom_aec.extrude`.
- `dt.energy.agent` tools call `custom_aec.modeling.api` and use `omni.usd`, `carb`, and `pxr`.
- `custom.aec.thermal_viz` mixes UI, viewport rendering, data models, data sources, MQTT input, and
  USD stage access inside one extension.
- Extension startup classes, UI windows, menus, and `extension.toml` files are correctly located
  under `source/extensions/` and must not move into `packages/`.

## 3. Architectural Role of `packages/`

Future `packages/` should hold reusable Python libraries that are:

- headless by default
- testable outside Omniverse Kit when possible
- importable by Kit extensions, backend services, scripts, and tests
- organized around stable domain concepts, not UI panels
- governed by explicit public APIs
- free of generated/runtime artifacts

`packages/` is the future destination for domain logic that outgrows a single Kit extension.

### 3.1 What belongs in `packages/`

Suitable package content:

- pure domain models
- validation rules
- geometry algorithms that can run without Kit, when possible
- AEC semantic contracts and metadata helpers
- EnergyPlus IDF generation logic separated from stage access
- simulation result models and parsers
- telemetry/time-series models
- agent message types, tool schemas, and routing abstractions that do not depend on Kit UI
- shared utility code used by more than one extension or service
- reusable test fixtures for package-level tests

### 3.2 What does not belong in `packages/`

Do not place these in `packages/`:

- Kit UI panels, windows, and widgets
- `omni.ext.IExt` startup classes
- `extension.toml` files
- app `.kit` descriptors
- extension-local `premake5.lua`
- extension icons, previews, and Kit registry metadata
- runtime outputs
- EnergyPlus simulation output directories
- generated IDF/ESO/CSV output artifacts
- large datasets
- trained models
- notebooks
- vendor binaries
- local developer configuration
- secrets
- generated artifacts
- pycache or bytecode

## 4. Difference From Other Repository Areas

### 4.1 `packages/` vs `source/extensions/`

`source/extensions/` is for Kit-integrated extension source. It owns extension manifests, startup
classes, UI, menu registration, Kit runtime integration, and extension-local assets.

`packages/` is for reusable Python libraries. Packages may be consumed by extensions, but should not
own extension startup, UI registration, or Kit manifest behavior.

### 4.2 `packages/` vs `backend/`

`packages/` contains libraries. `backend/` should contain service/process orchestration if introduced
later.

Backend services may depend on packages. Packages must not depend on backend runtime services.

### 4.3 `packages/` vs `scripts/`

`scripts/` should contain task entrypoints, one-off automation, or developer utilities.

Packages should contain importable, tested library code. Scripts may import packages; packages should
not import scripts.

### 4.4 `packages/` vs `schemas/`

`schemas/` should contain shared contracts if introduced later: JSON Schema, OpenAPI, USD metadata
schemas, message schemas, or tool contracts shared by Kit, backend, and tests.

Packages may use schemas, validate against schemas, or generate typed wrappers from schemas. Shared
schemas should not be buried inside one package if they are cross-boundary contracts.

## 5. Recommended Future Layout

Recommended package layout:

```text
packages/
  dt_core/
    pyproject.toml
    README.md
    src/
      dt_core/
        __init__.py
    tests/
  dt_geometry/
    pyproject.toml
    README.md
    src/
      dt_geometry/
        __init__.py
    tests/
  dt_aec/
    pyproject.toml
    README.md
    src/
      dt_aec/
        __init__.py
    tests/
```

Each package should be independently understandable and testable. A per-package `pyproject.toml` is
the conservative default until the project decides whether to use a monorepo package manager or a
single workspace-level packaging configuration.

Do not create these folders until an extraction ticket approves the boundary and validation plan.

## 6. Candidate Packages

### 6.1 `dt_core`

Purpose: shared primitives used across packages.

Expected public API:

- result objects
- error types
- path/identifier utilities
- lightweight validation helpers
- common dataclass or typing helpers

Allowed dependencies:

- Python standard library
- small pure-Python dependencies after approval

Forbidden dependencies:

- `omni`
- `carb`
- Kit UI
- extension modules under `source/extensions`
- backend services
- EnergyPlus binaries

Extraction candidates:

- generic result structure currently represented by `dt.energy.agent.tools.results`
- generic safety/path validation only if it can be made environment-neutral

Kit/pxr policy: no Kit or `pxr` dependency by default.

### 6.2 `dt_geometry`

Purpose: reusable geometry algorithms and mesh construction primitives.

Expected public API:

- polygon validation
- triangulation helpers
- primitive mesh descriptors
- extrusion algorithm inputs/outputs
- pure mesh data structures independent from USD authoring

Allowed dependencies:

- `dt_core`
- Python standard library
- numerical dependencies only after approval

Forbidden dependencies:

- `omni`
- `carb`
- UI modules
- extension modules under `source/extensions`
- direct stage mutation as a core package responsibility

Extraction candidates:

- pure calculations from `custom_aec.primitive_mesh.mesh_builder`
- pure calculations from `custom_aec.extrude.mesh_builder`
- polygon tests from modeling/sketching modules if isolated from USD

Kit/pxr policy: should avoid Kit runtime dependencies. A thin optional USD adapter may be considered
later, but core geometry should not require Kit.

### 6.3 `dt_aec`

Purpose: AEC semantic domain model and metadata conventions.

Expected public API:

- block, space, surface, opening, partition models
- AEC metadata names and validation rules
- AEC hierarchy conventions
- energy-preparation metadata contracts
- conversion between package models and USD adapter inputs

Allowed dependencies:

- `dt_core`
- `dt_geometry`
- schemas, if introduced

Forbidden dependencies:

- Kit UI
- extension startup modules
- backend services
- agent UI/tools as implementation dependencies

Extraction candidates:

- metadata rules from `custom_aec.modeling.api`
- opening and partition specs
- rebuild inputs/outputs after separating USD mutation from domain decisions
- AEC validation rules currently used by agent inspection and modeling tools

Kit/pxr policy: core should be headless. USD stage mutation should remain in extension adapters or a
separate optional adapter after an explicit decision.

### 6.4 `dt_energy`

Purpose: energy modeling domain concepts independent from a specific simulator.

Expected public API:

- thermal zone model
- construction/material abstractions
- surface boundary concepts
- energy model validation
- simulation request/response models

Allowed dependencies:

- `dt_core`
- `dt_aec`
- `dt_results`
- schemas, if introduced

Forbidden dependencies:

- Kit UI
- extension internals
- EnergyPlus binary runtime
- backend process orchestration

Extraction candidates:

- energy metadata assignment rules from `custom_aec.modeling.api`
- thermal validation concepts from `dt.energy.agent.tools.thermal_tools`
- parts of `thermal_sync_tools` only after separating USD stage writes

Kit/pxr policy: headless by default.

### 6.5 `dt_energyplus`

Purpose: EnergyPlus-specific adapters and IDF generation/parsing.

Expected public API:

- IDF document builder
- IDF export from `dt_energy`/`dt_aec` models
- EnergyPlus input validation
- adapter interfaces for running EnergyPlus, if not moved to backend

Allowed dependencies:

- `dt_core`
- `dt_aec`
- `dt_energy`
- `dt_results`
- external EnergyPlus Python libraries only after approval

Forbidden dependencies:

- Kit UI
- extension internals
- hardcoded local output paths
- direct dependence on vendored EnergyPlus binaries unless explicitly approved

Extraction candidates:

- `_build_placeholder_idf` from `dt.energy.agent.tools.idf_tools`
- future real IDF writer logic

Kit/pxr policy: should not depend on Kit. A Kit adapter should collect stage data and pass plain
models into this package.

### 6.6 `dt_results`

Purpose: simulation and analysis result models.

Expected public API:

- result metadata
- time-series result containers
- simulation status
- parsers for output summaries
- warnings/errors model

Allowed dependencies:

- `dt_core`

Forbidden dependencies:

- Kit UI
- extension internals
- backend services
- simulator process control

Extraction candidates:

- generic result objects from agent tools
- future EnergyPlus output parsers

Kit/pxr policy: no Kit dependency.

### 6.7 `dt_sensors`

Purpose: sensor and telemetry ingestion models independent from visualization UI.

Expected public API:

- sensor identity model
- telemetry source interfaces
- MQTT payload normalization
- CSV/JSON telemetry parsing
- zone-to-sensor binding contracts

Allowed dependencies:

- `dt_core`
- `dt_results` if time-series result models are shared

Forbidden dependencies:

- Kit UI
- viewport rendering
- extension startup
- direct dependency on `custom_aec.thermal_viz`

Extraction candidates:

- `TelemetrySeries`, `ZoneTelemetryBinding`, `TimeSeriesStore` from `timeseries.py`
- CSV/JSON telemetry source logic from `data_sources.py`
- pure MQTT payload parsing from `mqtt_client.py`

Kit/pxr policy: no Kit dependency.

### 6.8 `dt_ai`

Purpose: AI/agent orchestration that is not Kit UI-specific.

Expected public API:

- message types
- action routing abstractions
- tool registry contracts
- LLM provider interfaces
- intent parsing interfaces
- safety policy abstractions

Allowed dependencies:

- `dt_core`
- public schemas/contracts
- `dt_aec`, `dt_energy`, or `dt_results` only through public APIs

Forbidden dependencies:

- Kit UI
- private extension internals
- direct stage mutation as a hidden side effect
- secrets or provider-specific credentials

Extraction candidates:

- `message_types.py`
- `base_provider.py`
- `mock_provider.py`
- parts of `intent_parser.py`
- `ToolSpec` and schema definitions from `registry.py`
- action router only after tool execution is abstracted away from Kit-bound functions

Kit/pxr policy: no Kit dependency in core. Kit-specific tools should remain in extensions or adapters.

### 6.9 `dt_visualization`

Purpose: visualization models and color/comfort mapping that are not tied to Kit UI.

Expected public API:

- comfort band model
- color mapping rules in neutral types
- visualization state descriptors
- view-independent legend/scale metadata

Allowed dependencies:

- `dt_core`
- `dt_sensors`
- `dt_results`

Forbidden dependencies:

- ownership of AEC domain state
- Kit UI windows
- viewport scene mutation unless isolated in an adapter
- extension internals

Extraction candidates:

- pure comfort calculations from `thermal_style.py`
- view-independent visualization state from `custom.aec.thermal_viz`

Kit/pxr policy: core should be headless. Kit viewport rendering should stay in the extension or in a
future explicitly Kit-bound adapter, not in the pure package core.

## 7. Package Dependency Rules

Proposed dependency direction:

```text
dt_core
  <- dt_geometry
  <- dt_results
  <- dt_aec
       <- dt_energy
            <- dt_energyplus
  <- dt_sensors
       <- dt_visualization
  <- dt_ai
```

Rules:

- `dt_core` should depend on nothing project-specific.
- `dt_geometry` may depend on `dt_core`; it should avoid Kit runtime dependencies if possible.
- `dt_aec` may depend on `dt_core` and `dt_geometry`.
- `dt_energy` may depend on `dt_core`, `dt_aec`, and `dt_results`.
- `dt_energyplus` may depend on `dt_energy`, `dt_results`, and approved external EnergyPlus adapters.
- `dt_sensors` may depend on `dt_core` and optionally `dt_results`.
- `dt_visualization` may depend on `dt_core`, `dt_sensors`, and `dt_results`; it should avoid owning
  domain state.
- `dt_ai` should depend on public tool/service contracts, not UI extensions.
- Packages must not import from `source/extensions`.
- Packages must not use hidden imports that rely on Kit extension search paths.
- Cycles between packages are not allowed.

## 8. Relationship Between Packages and Kit Extensions

Kit extensions may import packages. Packages must not import Kit extension UI modules.

Recommended future pattern:

```text
source/extensions/custom.aec.modeling
  owns Kit startup, UI, commands, extension.toml, USD stage adapter
  imports dt_aec and dt_geometry public APIs

packages/dt_aec
  owns headless AEC model and validation rules

packages/dt_geometry
  owns pure geometry algorithms and mesh descriptors
```

Before extraction, the project must study:

- how package code becomes available inside Kit Python
- whether repo tooling needs prebuild/linking changes
- whether `extension.toml` needs dependency or path changes
- whether packages are editable installs, copied into `_build`, or added to a configured Python path
- whether package imports work in clean clone, build, and launch workflows

Extensions should depend on package public APIs. They should not reach into package private modules
for convenience.

## 9. Relationship Between Packages and Backend

Packages are reusable libraries. Backend code, if introduced, is service/process orchestration.

Rules:

- backend may depend on packages
- packages must not depend on backend services
- backend owns API serving, worker processes, queues, and external process orchestration
- packages own models, algorithms, validation, parsing, and library APIs
- EnergyPlus process execution may belong in backend if it becomes a long-running or isolated service

## 10. Relationship Between Packages and Tests

Package tests should be normal Python tests that run outside Kit when possible.

Recommended future layout:

```text
packages/dt_aec/tests/
packages/dt_geometry/tests/
packages/dt_energyplus/tests/
```

Rules:

- package tests should run without launching Kit unless the package is explicitly Kit-bound
- pure domain code should get unit tests before or during extraction
- Kit extension tests should remain under the extension or future integration test area
- extraction tickets must include smoke validation that affected extensions still load in Kit
- package tests should cover public APIs, not private implementation details only
- fixtures should be small, deterministic, and committed only when safe

## 11. Relationship Between Packages and Schemas

Future shared schemas should live outside packages if they are used across Kit, backend, API, and tests.

Recommended policy:

- packages may consume schemas as contracts
- packages may provide typed helpers around shared schemas
- package APIs should align with future `schemas/`
- schemas should not be duplicated inside multiple packages
- agent tool schemas should migrate toward shared contracts if they become external API boundaries

## 12. Migration and Extraction Policy

No extraction should occur during F1.1.

Future extraction rules:

1. Extract one package boundary at a time.
2. Start with the smallest high-value pure boundary.
3. Add tests before extraction when possible.
4. Keep extension public behavior stable.
5. Avoid moving UI and domain logic together.
6. Separate pure algorithms from Kit/USD adapters first.
7. Update imports deliberately; never use broad mechanical moves without validation.
8. Update docs and ADRs for accepted package boundaries.
9. Validate with package tests.
10. Validate with `repo.bat build`.
11. Validate with Kit launch and extension smoke tests when extensions are affected.
12. Confirm clean-clone reproducibility after packaging workflow changes.

## 13. Extraction Candidate Classification

| Current area | Recommendation | Future target | Notes |
| --- | --- | --- | --- |
| `custom_aec.primitive_mesh.mesh_builder` primitive shape calculations | Future package candidate; needs tests first | `dt_geometry` | Separate pure mesh data generation from USD stage authoring. Current module imports `pxr` and authors USD. |
| `custom_aec.extrude.mesh_builder` polygon extrusion and triangulation | Future package candidate; needs tests first | `dt_geometry` | Ear clipping, polygon validation, and mesh descriptors are good candidates; USD mutation should stay adapter-side. |
| `custom_aec.modeling.api` public AEC operations | Stay in extension for now; future split candidate | `dt_aec` plus Kit adapter | Current API depends on `omni.usd`, `carb`, `pxr`, and mesh builder extensions. Extract only after defining plain models. |
| `custom_aec.modeling.opening_specs` and `partition_specs` | Future package candidate; needs tests first | `dt_aec` | Metadata names and validation can become headless; USD attr writes may need adapter split. |
| `custom_aec.modeling.rebuild` and `rebuild_polygon` | Future package candidate in part; high-risk | `dt_aec` and `dt_geometry` | Contains domain decisions and USD mutation. Extract only after tests and behavior snapshots. |
| `dt.energy.agent.tools.idf_tools` IDF placeholder generation | Future package candidate; needs tests first | `dt_energyplus` | `_build_placeholder_idf` is package-suitable; stage inventory and output path handling remain adapter/tool concerns. |
| `dt.energy.agent.core.message_types` | Future package candidate | `dt_ai` or `dt_core` | Pure dataclasses are good early candidates if public API is stable. |
| `dt.energy.agent.core.action_router` | Future package candidate after adapter split | `dt_ai` | Currently depends on `carb` and concrete tool registry. Needs abstract tool executor boundary. |
| `dt.energy.agent.core.agent_controller` | Future package candidate after provider/tool boundary | `dt_ai` | Should depend on public LLM/tool interfaces, not concrete Kit tools. |
| `dt.energy.agent.core.safety` | Future package candidate in part | `dt_core` or `dt_ai` | Path validation can be shared, but local policy and environment assumptions need review. |
| `dt.energy.agent.tools.registry` and tool schemas | Future package candidate in part | `dt_ai` and future `schemas/` | `ToolSpec` and schemas are reusable; callable bindings to Kit tools should remain in extension/adapters. |
| `dt.energy.agent.tools.aec_modeling_tools`, `sketching_tools`, `thermal_sync_tools`, `scene_tools` | Stay in extension for now | Kit adapter layer | These are heavily Kit/USD-bound and call `omni.usd`, `omni.kit.commands`, `pxr`, and extension APIs. |
| `dt.energy.agent.tools.dxf_tools` | Future split candidate | `dt_geometry` plus Kit adapter | DXF parsing/geometry can be pure; stage import commands remain extension-bound. |
| `dt.energy.agent.tools.simulation_tools` | Future backend/service candidate | `backend/` or `dt_energyplus` adapter | Running EnergyPlus is likely process orchestration; keep minimal until simulator boundary is decided. |
| `custom_aec.thermal_viz.timeseries` | Future package candidate; good early target | `dt_sensors` or `dt_results` | Mostly pure dataclasses/store logic and should be testable outside Kit. |
| `custom_aec.thermal_viz.data_sources` | Future package candidate; needs tests | `dt_sensors` | CSV/JSON/live stub logic is mostly headless. |
| `custom_aec.thermal_viz.mqtt_client` | Future package or backend candidate; needs review | `dt_sensors` or backend service | Raw socket MQTT client may be reusable, but service lifecycle and security need review. |
| `custom_aec.thermal_viz.thermal_style` | Future package candidate in part | `dt_visualization` | Comfort bands and color mapping are reusable; `pxr.Gf` return types should be neutralized. |
| `custom_aec.thermal_viz.model_access`, `viewport_renderer`, `viewport_viz` | Stay in extension for now | Kit adapter layer | These depend on USD/viewport concepts and should not move into pure packages initially. |
| `custom_aec.thermal_viz.plot_widget`, `ui_telemetry`, `extension` | Should not extract to packages | Stay in extension | UI and extension lifecycle code. |

## 14. What Must Remain in `source/extensions/`

The following must remain extension-owned unless a future architecture decision creates a specific
Kit adapter package:

- `omni.ext.IExt` subclasses
- menu registration
- `omni.ui` windows/widgets
- Kit command integration
- `omni.usd.get_context()` access
- extension manifests
- extension-local assets and icons
- extension-level tests for Kit loading
- viewport renderer code that mutates USD stages
- app setup/template glue

## 15. Codex Access Policy for Future `packages/`

Codex may:

- edit package code when a ticket targets a package
- create a package only when a ticket explicitly approves the package boundary
- add or update package tests when package code changes
- update extension imports only in explicit extraction tickets
- document package APIs and migration steps

Codex must:

- run package tests when modifying package code
- run `repo.bat build` and Kit launch/smoke tests when package changes affect extensions
- keep packages from importing `source/extensions`
- preserve clean-clone reproducibility
- document packaging/path changes that affect Kit Python

Codex must not:

- create `packages/` during architecture-only tickets
- extract UI code into packages
- introduce hidden Kit path assumptions
- add package dependencies without approval
- move EnergyPlus binaries or outputs into packages
- commit generated package artifacts such as build wheels, `.egg-info`, pycache, or coverage output

## 16. Open Decisions

Open package decisions:

1. Packaging system: one workspace-level `pyproject.toml` versus per-package `pyproject.toml`.
2. Installation model: editable installs, repo prebuild linking, extension path injection, or Kit
   Python path configuration.
3. Namespace naming: distribution names like `dt-aec`/`dt_geometry` versus Python namespaces like
   `dt.aec`.
4. Whether `pxr` may be an optional dependency outside Kit, or whether all USD work stays in Kit
   adapters.
5. Whether EnergyPlus integration belongs primarily in `packages/`, `backend/`, or a split between
   `dt_energyplus` library code and backend process execution.
6. Whether AI/agent tools belong in `dt_ai`, backend services, extension adapters, or a layered split.
7. Public API stability expectations before extensions depend on packages.
8. Test framework and CI strategy for packages before first extraction.
9. Whether schemas should be introduced before package extraction to stabilize AEC, energy, telemetry,
   and tool contracts.
10. Whether package names should preserve the current `custom_aec` namespace or move to `dt_*`.

## 17. Risks

- Kit import risk: packages may not be visible inside Kit Python without repo/build configuration.
- Dependency risk: extracting code that imports `pxr`, `omni`, or `carb` may still require Kit runtime.
- Behavior risk: geometry and AEC rebuild code has visible scene-authoring behavior that can regress
  without tests.
- Coupling risk: agent tools currently reach directly into Kit stage state and extension APIs.
- Packaging churn risk: choosing the wrong packaging model early can create repeated migration work.
- Namespace risk: current extension names use `custom.aec.*` while Python packages use `custom_aec`;
  future `dt_*` packages need a deliberate naming decision.
- Public API risk: premature extraction can freeze unstable APIs.
- EnergyPlus boundary risk: simulator execution may be service/process orchestration rather than
  library behavior.

## 18. Recommended Future Tickets

Recommended next tickets:

1. Decide Python package naming and packaging model.
2. Add characterization tests around `custom_aec.thermal_viz.timeseries`.
3. Extract `dt_sensors` from pure thermal time-series/data-source logic as the first low-risk package,
   if approved.
4. Add tests for primitive and extrusion mesh algorithms before any geometry extraction.
5. Define schemas/contracts for AEC blocks, spaces, surfaces, telemetry bindings, and agent tools.
6. Design backend/service boundary for EnergyPlus execution before moving simulator code.
