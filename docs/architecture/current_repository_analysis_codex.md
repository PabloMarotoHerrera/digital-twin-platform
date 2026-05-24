# Current Repository Architecture Analysis

Date: 2026-05-24

This document is derived from direct inspection of the repository filesystem and code. The existing `current_repository_analysis.md` was not treated as source of truth.

## 1. Executive Summary

The repository is an NVIDIA Omniverse Kit App Template derivative that has been adapted into a custom USD authoring application named `my_own_software.kit`. The current architecture is a hybrid of three layers:

- Kit template infrastructure: `repo.bat`, `repo.sh`, `repo.toml`, `premake5.lua`, `_repo`, `tools`, `templates`, and generated `_build` outputs.
- Application source: `source/apps/my_own_software.kit`.
- Local domain extensions: AEC modeling, sketching, extrusion, primitive mesh generation, thermal visualization, and an energy-agent workflow under `source/extensions`.

The source side is relatively compact, but the repository also contains large generated/runtime surfaces: `_build`, `_compiler/current`, `_repo/repo.log`, generated tree dumps, `important_files.txt`, `repo_tree.txt`, `source_tree.txt`, `tools_tree.txt`, `extensions_list.txt`, and Python bytecode caches inside source folders.

The dominant architectural issue is unclear separation between source, generated artifacts, template inheritance, and experimental MVP code. The app directly enables all local extensions, while some extensions import other extensions' Python packages directly. This creates a workable but tightly coupled extension graph. The most notable coupling is `dt.energy.agent -> custom_aec.modeling -> custom_aec.extrude/custom_aec.primitive_mesh`, plus duplicated thermal synchronization logic between `custom_aec.modeling.api` and `dt.energy.agent.tools.thermal_sync_tools`.

EnergyPlus integration is not implemented as an executable integration. The current state is a placeholder IDF exporter plus a disabled `run_energyplus` tool. The code advertises future simulation behavior through the tool registry, but runtime execution is intentionally blocked.

No large migration should happen yet. The near-term architectural direction should be classification, cleanup of generated artifacts, formalization of extension boundaries, and stabilization of package naming and source/runtime ownership.

## 2. Repository Inventory

### Top-Level Structure

- `.git`, `.github`, `.vscode`: repository metadata and local/editor configuration.
- `docs`: project documentation. Before this document, it contained `07_USD_MODELING_CONVENTIONS.md`.
- `readme-assets`: NVIDIA/Kit README image and supplemental documentation assets.
- `source`: primary app and extension source.
- `templates`: Kit app/extension templates inherited from the upstream Kit App Template.
- `tools`: Packman/Repoman tooling and dependency manifests.
- `_repo`: repository tool dependency cache and logs.
- `_build`: generated build/runtime output, target dependencies, copied extensions, Kit SDK runtime, extension cache, logs, generated launch/test scripts.
- `_compiler`: symlink-like/current compiler pointer area; currently contains `current`, which produced read errors during recursive enumeration.
- Root guidance files: `00_PROJECT_CONTEXT.txt` through `07_PROFESIONAL_VISUALIZATION.txt`, `digital_twin_contexto_maestro.md`, `current_repository_analysis.md`.
- Generated inventory files: `important_files.txt`, `repo_tree.txt`, `source_tree.txt`, `tools_tree.txt`, `extensions_list.txt`, `templates/templates_tree.txt`.
- Vendor/archive artifact: `CustomPrimitiveMesh.zip`.
- Kit legal/readme files: `LICENSE`, `PRODUCT_TERMS_OMNIVERSE`, `SECURITY.md`, `CHANGELOG.md`, `README.md`.

### Source Structure

`source` contains:

- `source/apps/my_own_software.kit`: active Kit application descriptor.
- `source/apps/my_own_software.kit.before_extension_cleanup`: prior app descriptor snapshot.
- `source/extensions`: all local extensions.
- `source/rendered_template_metadata.json`: auto-generated template metadata.
- `source/source_tree.txt`: generated tree dump inside source.

### Local Extensions

Detected local extension folders:

- `custom.aec.sketch`
- `custom.aec.primitive_mesh`
- `custom.aec.extrude`
- `custom.aec.modeling`
- `custom.aec.thermal_viz`
- `dt.energy.agent`
- `my_company.my_usd_composer_setup_extension`

### Runtime and Generated Areas

`_build` contains:

- `_build/apps/exts.deps.generated.kit`: generated dependency Kit file.
- `_build/generated/prebuild.toml`: generated prebuild state.
- `_build/host-deps`: linked host tools such as Premake and Python.
- `_build/target-deps`: linked target dependencies including Python, pybind11, doctest, fmt, and Carb SDK plugins.
- `_build/windows-x86_64/debug`: generated launch/test batch files and dev metadata.
- `_build/windows-x86_64/release`: runtime app layout, copied local extensions in `exts`, external extension cache in `extscache`, Kit runtime link, logs, sitecustomize, generated launch/test scripts.

`_repo` contains repo-tool dependencies such as `repo_build`, `repo_kit_tools`, `repo_man`, `repo_package`, `repo_test`, and `repo_usd`, plus a large `repo.log`.

## 3. Architectural Layers Detected

### Layer 1: Kit Tooling and Template Inheritance

The repo imports upstream Kit template configs in `repo.toml`:

- `_repo/deps/repo_kit_tools/kit-template/repo.toml`
- `_repo/deps/repo_kit_tools/kit-template/repo-external-app.toml`

The root `premake5.lua` uses:

- `omni/repo/build`
- `_repo/deps/repo_kit_tools/kit-template/premake5-kit`
- `kit.setup_all({ cppdialect = "C++17" })`
- `define_app("my_own_software.kit")`

This means the repository behavior is not fully local. Build, launch, package, extension discovery, and generated scripts are inherited from Kit template tooling.

### Layer 2: Application Descriptor

`source/apps/my_own_software.kit` is the application composition layer. It declares the app package, renderer/window defaults, persistent settings, extension folders, and the local extension dependency set.

The app still identifies its template origin:

- `template_name = "omni.usd_composer"`
- `[template] type = "ApplicationTemplate"`
- generated version-lock block for Kit SDK `109.0.3+production.263267.62477c11.gl`

### Layer 3: Setup Extension

`my_company.my_usd_composer_setup_extension` is still active and loaded at order `1000`. It owns app setup behavior such as stage defaults, layout, menu layout, startup verification, title/icon usage, and template-derived USD Composer setup behavior.

This extension is both a template remnant and an active integration point.

### Layer 4: AEC Authoring Extensions

The AEC source is split into:

- `custom.aec.sketch`: curve/sketch authoring.
- `custom.aec.primitive_mesh`: primitive mesh generation.
- `custom.aec.extrude`: closed curve to mesh/block extrusion.
- `custom.aec.modeling`: unified modeling panel, rebuild logic, metadata, energy preparation, and public API.

The modeling extension is the functional center of the AEC source layer. It imports mesh builders from primitive/extrude extensions and exposes `custom_aec.modeling.api`.

### Layer 5: Thermal Visualization

`custom.aec.thermal_viz` owns thermal/telemetry UI and viewport visualization:

- CSV/JSON telemetry ingestion.
- Synthetic/live stub time series.
- MQTT client implemented with raw sockets and a background thread.
- Plot widget and viewport renderer.
- A sample CSV in extension `data`.

It does not declare a dependency on `custom.aec.modeling`, but it expects AEC spaces and metadata conventions created by modeling code.

### Layer 6: Energy Agent

`dt.energy.agent` provides a chat/agent workflow over the AEC model. It contains:

- `core`: action routing, safety, message types, controller.
- `llm`: mock provider, intent parser, placeholder NVIDIA NIM provider.
- `tools`: scene inspection, AEC modeling tools, sketching tools, DXF import/reference tools, IDF placeholder export, disabled EnergyPlus runner, thermal sync tools.
- `ui`: chat window.
- `mcp`: tool schema facade.

The agent is explicitly dependent on modeling, primitive mesh, and extrusion extensions in `extension.toml`.

## 4. Extension Analysis

### `custom.aec.sketch`

Purpose:

- Sketch/curve authoring for AEC workflows.
- Uses `omni.curve.manipulator`, `omni.kit.commands`, `omni.kit.menu.utils`, and `omni.usd`.

Package naming:

- Extension name: `custom.aec.sketch`
- Python module: `custom.aec.sketch`
- On-disk package: `custom/aec/sketch`

Observations:

- This extension follows the dotted Python package implied by the extension name.
- It still includes default template test files (`test_hello.py`, `test_benchmarks.py`).
- Its package naming differs from most later AEC extensions, which use `custom_aec.*`.

### `custom.aec.primitive_mesh`

Purpose:

- Parametric primitive mesh tools for AEC modeling.
- Contains `mesh_builder.py` and UI extension code.

Package naming:

- Extension name: `custom.aec.primitive_mesh`
- Python module: `custom_aec.primitive_mesh`
- On-disk package: `custom_aec/primitive_mesh`

Observations:

- Uses a namespace package root `custom_aec` with `pkgutil.extend_path`.
- Exposes mesh generation used by `custom.aec.modeling`.
- Coupled to USD/PXR mesh authoring.

### `custom.aec.extrude`

Purpose:

- Extrudes closed AEC sketch curves into USD mesh blocks.

Package naming:

- Extension name: `custom.aec.extrude`
- Python module: `custom_aec.extrude`

Observations:

- Its `mesh_builder.py` is imported directly by `custom_aec.modeling`.
- It overlaps conceptually with modeling rebuild/extrusion responsibilities.

### `custom.aec.modeling`

Purpose:

- Unified AEC modeling panel and public API for blocks, sketches, spaces, surfaces, partitions, openings, rebuilds, energy metadata, and thermal visualization readiness.

Package naming:

- Extension name: `custom.aec.modeling`
- Python module: `custom_aec.modeling`

Important files:

- `extension.py`: large UI/control file.
- `api.py`: public-ish programmatic surface used by `dt.energy.agent`.
- `rebuild.py`, `rebuild_polygon.py`: geometry rebuild behavior.
- `partition_specs.py`, `opening_specs.py`: metadata/spec helpers.

Observations:

- This extension is currently the central domain boundary, but it is also a UI extension and domain API provider.
- It imports implementation functions from `custom_aec.extrude` and `custom_aec.primitive_mesh`.
- It implements `sync_block_to_thermalviz`, thermal material creation, and AEC energy metadata defaults, which overlap with `dt.energy.agent.tools.thermal_sync_tools`.
- It defines fixed USD hierarchy conventions such as `/World/Building`, `/World/Building/Sketches`, `/World/Building/Materials/Thermal`, and `/World/Building/_ThermalViz`.

### `custom.aec.thermal_viz`

Purpose:

- Thermal visualization and telemetry overlay for AEC spaces.

Package naming:

- Extension name: `custom.aec.thermal_viz`
- Python module: `custom_aec.thermal_viz`

Important files:

- `extension.py`: main UI and orchestration.
- `viewport_renderer.py`: viewport coloring/materialization.
- `data_sources.py`: CSV/JSON/live source ingestion.
- `mqtt_client.py`: raw MQTT socket client.
- `plot_widget.py`, `timeseries.py`, `signals.py`, `thermal_style.py`.

Observations:

- It is a thermal visualization extension, but it also owns live data ingestion concerns.
- The README still calls MQTT a future driver in one section while also documenting current MQTT mode later, indicating documentation drift.
- It has no explicit extension dependency on `custom.aec.modeling`, despite relying on AEC spaces and attributes.
- It includes sample telemetry data in `data/sample_temperature_day.csv`.

### `dt.energy.agent`

Purpose:

- Agent/chat workflow for inspecting and authoring early energy-model data in USD.

Package naming:

- Extension name: `dt.energy.agent`
- Python module: `dt.energy.agent`

Important files:

- `tools/registry.py`: central tool registry.
- `tools/idf_tools.py`: placeholder IDF export.
- `tools/simulation_tools.py`: disabled EnergyPlus runner.
- `tools/dxf_tools.py`: DXF reference import and snap-point helpers.
- `tools/sketching_tools.py`: sketch tools and rebuild helpers.
- `tools/thermal_sync_tools.py`: thermal synchronization.
- `core/safety.py`: tool confirmation and output path validation.
- `llm/intent_parser.py`: rule-based intent parsing.

Observations:

- The agent imports `custom_aec.modeling.api`, creating a direct Python dependency beyond extension-level TOML dependencies.
- The tool registry contains compatibility aliases and not-yet-implemented tools, which is useful for roadmap continuity but blurs what is production-ready.
- `run_energyplus` is marked dangerous/requires confirmation and is blocked by `is_tool_allowed`, but it is also implemented as a disabled stub.
- The NVIDIA NIM provider is a placeholder and does not call NIM yet.

### `my_company.my_usd_composer_setup_extension`

Purpose:

- USD Composer setup extension inherited from the Kit template and customized for this app.

Package naming:

- Extension name: `my_company.my_usd_composer_setup_extension`
- Python module: `my_company.my_usd_composer_setup_extension`

Observations:

- Contains NVIDIA template licensing headers and template-derived metadata.
- Owns app defaults, menu/layout behavior, stage defaults, and startup verification.
- Contains stage template `zup_default_stage.py`, layout JSON, MDL flattener materials, and built-in materials.
- Still points repository metadata at `https://github.com/NVIDIA-Omniverse/kit-app-template`.
- As currently used, it is not just template residue; it is active app glue.

## 5. Runtime / Build Analysis

### Repo Tooling

`repo.bat` bootstraps through `tools/packman/python.bat` and `tools/repoman/repoman.py`. It sets `OMNI_REPO_ROOT` and optionally uses `repo-cache.json` for Packman package root configuration.

`repo.toml` inherits most behavior from Kit template configs. Local repo-specific behavior includes:

- Ensuring `source/apps` exists during fetch.
- Disabling Windows native build with `[repo_build.build]."platform:windows-x86_64".enabled = false`.
- Copying `tools/deps/user.toml` into `_build/deps/user.toml`.
- Pre-caching extensions for `source/apps/my_own_software.kit`.
- Package definitions for fat/thin packages.
- Enabling launch, app packaging, and container packaging tooling.

### Premake Structure

Root `premake5.lua`:

- Loads repo build tooling.
- Initializes Kit template premake tooling.
- Copies `tools/deps/user.toml`.
- Defines only one app: `my_own_software.kit`.

Each local extension has a small `premake5.lua` that calls `project_ext(ext)` and `repo_build.prebuild_link` to link selected source folders into the generated extension target directory.

This is a source-to-runtime link/copy architecture. The source extension folder is not the final runtime folder; `_build/windows-x86_64/release/exts/<extension>` is.

### App Runtime

The active app is `source/apps/my_own_software.kit`.

It enables local extension folders through:

- `${app}/../exts`
- `${app}/../extscache`

At runtime inside `_build/windows-x86_64/release`, the app sees:

- `apps`
- `exts` for generated/local extensions
- `extscache` for cached registry extensions
- `kit` for Kit SDK runtime
- `logs`, `data`, `cache`, `site`, and package license folders

### Generated Version Lock

`source/apps/my_own_software.kit` contains a generated section:

- Kit SDK version: `109.0.3+production.263267.62477c11.gl`
- Exact dependency: `omni.kit.window.modifier.titlebar-107.0.2`
- Version lock list for selected dependencies.

This means the app descriptor is partly authored and partly generated. Edits around the generated block carry regeneration risk.

### External Registries

`repo_precache_exts.registries` points to:

- `kit/default` on `ovextensionsprod.blob.core.windows.net`
- `kit/sdk` on `ovextensionsprod.blob.core.windows.net`
- `kit/community` on CloudFront

The local application depends on external registry availability during fetch/precache/update flows unless caches are already populated.

## 6. Dependency Observations

### Extension Dependency Direction

Declared app dependency direction:

`my_own_software.kit` -> all local extensions and many Kit extensions.

Declared local extension direction:

- `custom.aec.modeling` -> `custom.aec.extrude`, `custom.aec.primitive_mesh`, Kit UI/USD dependencies.
- `dt.energy.agent` -> `custom.aec.modeling`, `custom.aec.primitive_mesh`, `custom.aec.extrude`, Kit UI/USD dependencies.
- `custom.aec.thermal_viz` -> only Kit UI/USD dependencies.
- `custom.aec.sketch` -> curve manipulator and USD dependencies.
- `my_company.my_usd_composer_setup_extension` -> setup/layout/menu/property/title/stage-template dependencies.

### Python Import Direction

Observed direct imports:

- `custom_aec.modeling.api` imports `custom_aec.extrude.mesh_builder` and `custom_aec.primitive_mesh.mesh_builder`.
- `custom_aec.modeling.extension` imports the same primitive/extrude helpers.
- `dt.energy.agent.tools.aec_modeling_tools`, `thermal_sync_tools`, and `sketching_tools` import `custom_aec.modeling.api`.
- Thermal visualization primarily imports internally and uses USD/PXR APIs directly.

### Directional Concerns

- `custom.aec.modeling` acts as both UI and domain service.
- `dt.energy.agent` has direct knowledge of modeling API internals and USD hierarchy conventions.
- Thermal visualization relies on AEC model conventions but does not declare the dependency.
- `custom_aec` is used as a namespace package across multiple extensions. This is workable in Kit but requires careful extension load ordering and package collision management.
- `custom.aec.sketch` uses `custom.aec.sketch`, while other custom AEC extensions use `custom_aec.*`. This is an inconsistent package boundary.

## 7. Structural Problems

### Source vs Runtime Separation Is Blurred

The repository contains generated/runtime material alongside source:

- `_build` is present and large.
- `_repo/repo.log` is present.
- `_compiler/current` exists and caused recursive enumeration read errors.
- `source` contains `source_tree.txt`.
- Root contains generated inventory dumps.
- Python `__pycache__` folders exist inside `source/extensions`.

This makes repository inspection noisy and increases the chance that generated state is mistaken for source.

### Pycache Pollution

Python bytecode caches were found inside source extension packages, including:

- `custom.aec.extrude`
- `custom.aec.modeling`
- `custom.aec.primitive_mesh`
- `custom.aec.sketch`
- `custom.aec.thermal_viz`
- `dt.energy.agent`
- `my_company.my_usd_composer_setup_extension`

There were 14 `__pycache__` directories under `source`, and thousands of `.pyc` files repository-wide when including `_build`/tool/runtime areas.

### Duplicated Responsibilities

Duplicated or overlapping responsibilities include:

- Thermal synchronization in `custom_aec.modeling.api.sync_block_to_thermalviz` and `dt.energy.agent.tools.thermal_sync_tools`.
- Energy metadata defaults in modeling API, agent thermal tools, and AEC inspection/validation.
- Sketch/rebuild behavior in `custom_aec.modeling` and `dt.energy.agent.tools.sketching_tools`.
- Placeholder thermal zone language in agent tools while actual model hierarchy uses AEC blocks/spaces.
- Setup extension and app descriptor both configure app defaults, stage templates, window behavior, renderer behavior, and persistent settings.

### Naming Inconsistencies

- App name: `my_own_software`, still generic.
- Setup extension name: `my_company.my_usd_composer_setup_extension`, still template-derived.
- AEC extension names: `custom.aec.*`.
- Python packages: mixed `custom.aec.sketch`, `custom_aec.*`, `dt.energy.agent`, and `my_company.*`.
- Root docs include Spanish and English naming, while code and app package names are mostly English/template-derived.

### Experimental and Production Code Are Mixed

MVP and future/research areas are inside active app extensions:

- Disabled EnergyPlus execution.
- Placeholder IDF exporter.
- Placeholder NIM provider.
- Future tool registry entries marked `implemented=False`.
- DXF parser fallback and incomplete DXF-to-sketch tools.
- Raw MQTT implementation.

These are useful experiments but not isolated from the loaded application.

### Template Metadata Drift

Several files still point to upstream Kit template ownership or generic template names:

- Extension repository URLs reference NVIDIA Kit App Template.
- Setup extension is still `my_company.my_usd_composer_setup_extension`.
- `source/rendered_template_metadata.json` includes an old `try.one` extension reference not present in active `source/extensions`.
- `source/apps/my_own_software.kit.before_extension_cleanup` remains beside the active app descriptor.

### Large App Descriptor Surface

`my_own_software.kit` directly owns many settings and dependencies. It includes a generated block and a broad list of local and Kit dependencies. This makes app-level changes risky because local app behavior, upstream Kit version-locking, and extension composition all live in one file.

## 8. Migration Risks

### Breaking Kit Template Tooling

The repository depends heavily on inherited Kit template configs. Moving or renaming `source/apps`, `source/extensions`, `tools`, `_repo`, `repo.toml`, or `premake5.lua` without understanding `repo_kit_tools` assumptions may break:

- `repo build`
- app launch script generation
- extension prebuild linking
- package creation
- precache behavior
- generated test scripts

### Breaking Namespace Package Composition

Multiple extensions contribute to the `custom_aec` namespace. If packages are moved or renamed without preserving namespace behavior, imports like `custom_aec.modeling`, `custom_aec.extrude`, and `custom_aec.primitive_mesh` may fail.

### Extension Load Ordering

Direct Python imports across extensions require the providing extension to be enabled and importable before consumers execute. The TOML dependencies cover some of this, but undeclared convention dependencies remain, especially thermal visualization's dependency on AEC model structure.

### Generated App Descriptor Regeneration

The generated section in `my_own_software.kit` can be regenerated by Kit tooling. Manual changes in or around that block may be lost or conflict with future version-lock generation.

### Runtime Artifact Confusion

If `_build/windows-x86_64/release/exts` is edited instead of `source/extensions`, changes may be lost on prebuild/regeneration. Conversely, if generated outputs are committed or treated as canonical, future changes may conflict with source regeneration.

### EnergyPlus Hardening Risk

Turning `run_energyplus` from stub into subprocess execution introduces security and reproducibility risks:

- Executable discovery.
- IDF/EPW validation.
- Output directory control.
- Long-running process lifecycle.
- UI responsiveness.
- Confirmation and sandbox policy.
- Mapping EnergyPlus outputs back into USD/thermal visualization.

### USD Schema Convention Lock-In

Current code authors ad hoc `aec:*` attributes and fixed paths. Any later formal schema or hierarchy migration must account for:

- `/World/Building`
- `/World/Building/Sketches`
- `/World/Building/Materials/Thermal`
- `/World/Building/_ThermalViz`
- block child paths such as `Mass`, `Spaces/Space_01`, `Surfaces`, `Partitions`, `Metadata`.

## 9. Recommended Architectural Directions

These are directions for classification and stabilization, not large migrations.

### Classify Source, Generated, Runtime, and Vendor Areas

Document ownership categories explicitly:

- Source of truth: `source/apps`, `source/extensions`, selected project docs.
- Kit-managed tooling: `tools`, `_repo/deps`, root `repo.*`, root `premake5.lua`.
- Generated/runtime: `_build`, `_compiler`, `_repo/repo.log`, generated tree/list dumps, `__pycache__`.
- Template library: `templates`, `readme-assets`.
- External/vendor/archive: `CustomPrimitiveMesh.zip`, Kit SDK/runtime caches, extension cache.

### Stabilize Extension Boundaries

Keep the current extension split for now, but define intended ownership:

- `custom.aec.modeling`: AEC domain API and authoring workflows.
- `custom.aec.primitive_mesh`: primitive mesh implementation detail.
- `custom.aec.extrude`: extrusion implementation detail.
- `custom.aec.sketch`: interactive sketch authoring.
- `custom.aec.thermal_viz`: visualization and telemetry.
- `dt.energy.agent`: orchestration/chat/tool facade, not duplicate domain implementation.
- setup extension: app setup only.

### Reduce Duplicate Domain Logic Over Time

Without restructuring immediately, prefer one source of truth for:

- Thermal material creation.
- ThermalViz registry creation.
- Energy metadata defaults.
- IDF export readiness validation.
- AEC USD hierarchy constants.

The natural current candidate is `custom_aec.modeling.api`, because the agent already imports it.

### Make Experimental Status Explicit

Mark experimental/research surfaces in documentation and UI expectations:

- EnergyPlus runner is disabled.
- IDF export is placeholder/non-runnable.
- NIM provider is placeholder.
- Some DXF tools are fallback/prototype only.
- MQTT is hand-rolled MVP ingestion, not a hardened integration layer.

### Preserve Kit Template Inheritance While Reducing Drift

Do not remove Kit template structure yet. Instead:

- Record which files are template-managed.
- Avoid editing generated Kit blocks by hand.
- Keep `repo.toml` and `premake5.lua` changes minimal and explicit.
- Rename/replace template-derived identifiers only after dependency and packaging assumptions are known.

### Clean Generated Artifacts Separately

Treat cleanup as a future controlled task, not part of this analysis. Candidate cleanup categories:

- `__pycache__` under `source`.
- generated `*_tree.txt` and `important_files.txt` files if not intentionally tracked.
- stale `source/apps/my_own_software.kit.before_extension_cleanup`.
- stale `source/rendered_template_metadata.json` references.

### Formalize Python Package Naming

Future work should decide whether AEC packages use:

- dotted package names matching extension names, e.g. `custom.aec.*`; or
- namespace root `custom_aec.*`.

The current mixed model is functional but confusing for extension boundaries and import ownership.

## 10. Questions / Ambiguities Detected

- Is `my_own_software.kit` the final app name, or still a placeholder?
- Should `my_company.my_usd_composer_setup_extension` remain as the setup extension name, or is it template residue awaiting product naming?
- Are root files such as `important_files.txt`, `repo_tree.txt`, `source_tree.txt`, `tools_tree.txt`, and `extensions_list.txt` intended tracked artifacts or temporary analysis dumps?
- Is `_build` intended to remain in the repository/worktree for local development only, or should it be treated as disposable generated output?
- Is `CustomPrimitiveMesh.zip` a required vendor artifact, historical backup, or migration input?
- Should `custom.aec.thermal_viz` explicitly depend on `custom.aec.modeling`, given its reliance on AEC spaces and metadata?
- Should `dt.energy.agent.tools.thermal_sync_tools` delegate fully to `custom_aec.modeling.api.sync_block_to_thermalviz`?
- Should EnergyPlus integration target a local executable path, bundled dependency, external service, or user-configured installation?
- What is the intended persistence model for EnergyPlus output and telemetry output: USD attributes, sidecar files, app cache, or external database?
- Should DXF import remain inside the agent extension, or become an AEC import/sketch extension capability?
- Is the `custom_aec` namespace package strategy intentional for shared AEC modules, or an artifact of template-generated extension creation?
- Are current tests template placeholders, real smoke tests, or both?
- Should `templates` remain in this product repo, or is it retained only because the repo still functions as a Kit App Template derivative?
