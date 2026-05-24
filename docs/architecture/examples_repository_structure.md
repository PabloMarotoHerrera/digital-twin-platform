# Examples Repository Structure Contract

Status: proposed architecture contract  
Scope: future root `examples/` structure only  
Date: 2026-05-24  

## 1. Purpose

This document defines the intended future root-level `examples/` structure for minimal reproducible
examples, demos, tutorial workflows, sample projects, and reference scenarios.

This is a design contract only. It does not create `examples/`, move sample files, edit source, change
Kit integration, stage, commit, or push.

The current repository is an NVIDIA Omniverse Kit App Template derivative. The current product
source-of-truth remains under `source/apps` and `source/extensions`. Future reusable code belongs in
`packages/`, future backend orchestration belongs in `backend/`, and future executable tests belong in
`tests/`. Examples must not blur those ownership boundaries.

## 2. Current Example and Sample State Observed

There is currently no root-level `examples/` directory.

Current sample-like files and folders are extension-owned:

```text
source/extensions/custom.aec.thermal_viz/data/sample_temperature_day.csv
source/extensions/custom.aec.sketch/data/icon.png
source/extensions/custom.aec.sketch/data/preview.png
source/extensions/custom.aec.sketch/docs/README.md
source/extensions/custom.aec.sketch/docs/Overview.md
source/extensions/custom.aec.sketch/docs/CHANGELOG.md
source/extensions/custom.aec.thermal_viz/README.md
source/extensions/my_company.my_usd_composer_setup_extension/data/BuiltInMaterials.usda
source/extensions/my_company.my_usd_composer_setup_extension/data/flattener_materials/*.mdl
source/extensions/my_company.my_usd_composer_setup_extension/data/stage_templates/zup_default_stage.py
source/extensions/my_company.my_usd_composer_setup_extension/layouts/default.json
```

Observed characteristics:

- `sample_temperature_day.csv` is a small telemetry sample used by the thermal visualization extension.
- `icon.png` and `preview.png` are extension metadata/registry assets, not general examples.
- `zup_default_stage.py` is a Kit stage template asset used by the setup extension.
- setup extension material assets are application/setup assets, not tutorial examples.
- `custom.aec.thermal_viz/README.md` contains usage examples and telemetry payload snippets.
- `custom.aec.sketch/docs/README.md` describes the extension as an example/template extension.
- Root owner-decision files may contain workflow/example material, but they require owner review before
  being promoted into public examples or docs.

## 3. Architectural Role of Future Root `examples/`

Future root `examples/` should hold runnable or loadable example artifacts that demonstrate how to use
the platform without being part of production source, test assertions, generated outputs, or private
data.

Root examples should be:

- minimal
- reproducible from a clean clone when dependencies are available
- public-safe
- documented with usage instructions
- small enough for normal Git unless explicitly artifact-managed
- stable enough to be useful for users and future smoke workflows

Root examples should demonstrate usage. They should not assert correctness as their primary purpose.
Correctness belongs in tests.

## 4. What Belongs in Root `examples/`

Suitable future root examples:

- minimal Omniverse/Kit workflows
- small USD/USDA scenes demonstrating AEC conventions
- tiny telemetry CSV/JSON samples used in tutorials
- small IDF snippets or EnergyPlus example inputs after license review
- AI agent prompt/tool usage examples
- backend job request examples after backend exists
- end-to-end demo manifests that reference small committed inputs
- README-driven tutorial workflows
- sample configuration templates that are not secrets and not local machine-specific

## 5. What Does Not Belong in Root `examples/`

Do not place these in root `examples/`:

- production Kit extension code
- extension startup classes
- extension manifests
- app `.kit` descriptors
- generated runtime outputs
- `_build`, `_repo`, or `_compiler` artifacts
- EnergyPlus simulation output folders
- large generated datasets
- trained models or checkpoints
- notebooks as the primary example format
- private building data
- real sensor data without anonymization and owner approval
- vendor binaries
- licensed vendor examples without permission
- secrets
- local machine configuration
- temporary debugging files

## 6. Difference From Related Areas

### 6.1 `examples/` vs `docs/examples/`

Root `examples/` contains runnable or loadable artifacts and workflows.

`docs/examples/` should contain explanatory snippets, short command examples, and prose that supports
documentation. Documentation may link to root examples, but should not duplicate large payloads.

### 6.2 `examples/` vs extension-local `data/`

Extension-local `data/` belongs to the extension runtime or extension metadata.

Keep assets extension-local when they are required by:

- Extension Manager metadata
- extension icons/previews
- app setup behavior
- stage templates registered by the extension
- extension-specific runtime sample data
- extension tests or UI demos that ship with the extension

Move or copy to root `examples/` only when the asset becomes a general platform example independent of
one extension's runtime packaging.

### 6.3 `examples/` vs `tests/fixtures/`

Examples demonstrate usage. Test fixtures support assertions.

An example input may be reused by tests only when it is small, stable, public-safe, and intentionally
treated as both example and fixture. Tests must not depend on examples that are expected to change for
tutorial clarity.

### 6.4 `examples/` vs `data/`

Future `data/` should contain curated datasets or small data assets with a data governance policy.

Root `examples/` should contain tiny sample inputs for human workflows, not dataset collections.

### 6.5 `examples/` vs `runs/` and `outputs/`

Root `examples/` may contain input files and expected descriptions.

Generated outputs belong in future `runs/` or `outputs/`. Example outputs may be committed only if
they are tiny, canonical, public-safe, and explicitly approved.

### 6.6 `examples/` vs `references/`

Future `references/` should contain external reference summaries, citations, or links.

Root `examples/` should contain artifacts that can be used with the repository. Do not copy external
reference projects or vendor examples into `examples/` unless license, size, and provenance are clear.

## 7. Proposed Future Root Layout

Recommended future layout:

```text
examples/
  README.md
  omniverse/
  backend/
  integration/
  datasets/
  usd/
  energyplus/
  telemetry/
  ai_agent/
  demos/
```

Create these folders only when examples are approved. This ticket does not create them.

## 8. Example Category Policy

### 8.1 `examples/README.md`

Purpose: index and entry point for all examples.

Should include:

- example list
- required dependencies
- expected runtime
- commands to run/load
- expected outputs
- public/private data notes
- whether the example is smoke-testable

### 8.2 `examples/omniverse/`

Purpose: Omniverse/Kit examples.

Examples:

- load a small USD scene in `my_own_software.kit`
- demonstrate AEC extension workflow manually
- show extension interaction using a minimal scene

Ownership: Kit integration/examples.

Must not include production extension source.

### 8.3 `examples/backend/`

Purpose: backend request/config examples after backend exists.

Examples:

- local backend job request JSON
- fake EnergyPlus run request
- backend config example linked to `.env.example`

Ownership: backend examples.

Must not include generated run outputs or secrets.

### 8.4 `examples/integration/`

Purpose: cross-layer examples.

Examples:

- USD/AEC model exported to backend job input
- backend result imported into a visualization workflow
- Kit extension calling a documented backend adapter

Ownership: cross-layer architecture.

Should be small and smoke-testable only after the underlying layers are stable.

### 8.5 `examples/datasets/`

Purpose: tiny example dataset manifests or slices.

Examples:

- miniature synthetic telemetry set
- tiny manifest showing expected dataset metadata

Ownership: data/dataset examples.

Must not become bulk dataset storage.

### 8.6 `examples/usd/`

Purpose: small USD/USDA scenes illustrating platform conventions.

Examples:

- minimal `/World/Building` hierarchy
- one block with spaces/surfaces
- small AEC metadata example

Ownership: AEC/USD examples.

Prefer USDA for readability when possible.

### 8.7 `examples/energyplus/`

Purpose: small EnergyPlus-related example inputs.

Examples:

- tiny IDF snippet generated from a minimal AEC model
- sample job manifest that references an IDF and weather file path
- small expected IDF text output from a package builder

Ownership: EnergyPlus/backend examples.

EPW/weather files require license and size review before commit.

### 8.8 `examples/telemetry/`

Purpose: small telemetry examples.

Examples:

- CSV playback sample
- JSON playback sample
- MQTT payload examples
- zone-to-sensor binding example

Ownership: telemetry/sensor examples.

Synthetic data is preferred.

### 8.9 `examples/ai_agent/`

Purpose: AI agent usage examples.

Examples:

- safe prompt examples
- tool-call request/response examples
- agent workflow snippets

Ownership: agent/tooling examples.

Must not include real credentials, private prompts, or live provider secrets.

### 8.10 `examples/demos/`

Purpose: curated end-to-end demos.

Examples:

- minimal AEC modeling to thermal visualization demo
- future AEC to EnergyPlus to result visualization demo

Ownership: product/demo.

Demos should reference small inputs and write outputs to `runs/` or `outputs/`, not into `examples/`.

## 9. Size and Reproducibility Rules

Examples must:

- be small
- be deterministic when possible
- avoid private data
- avoid local absolute paths
- include README or usage instructions
- state required commands
- state expected outputs
- state required app/backend/package dependencies
- state whether generated outputs are expected
- avoid committing generated outputs by default

Examples should be runnable or loadable from a clean clone when required dependencies are available.
If an example requires optional dependencies such as EnergyPlus, that requirement must be explicit.

## 10. Example Asset Policy

### 10.1 USD/USDA

- Prefer small synthetic USDA files for readability.
- Avoid private building geometry.
- Include AEC convention notes when relevant.
- Keep binary USD files only when necessary.

### 10.2 IDF

- Tiny IDF snippets may be committed after review.
- Generated IDFs are outputs unless explicitly promoted as canonical examples.
- IDF examples must state whether they are runnable or illustrative.

### 10.3 Telemetry CSV/JSON

- Synthetic samples are preferred.
- Keep files small.
- Include timestamp/channel conventions.
- Do not commit real sensor data without anonymization and owner approval.

### 10.4 Sample configs

- Commit example configs only.
- Do not include secrets.
- Do not include machine-specific absolute paths.
- Use placeholders and environment variable names.

### 10.5 Images and screenshots

- Screenshots may support demos, but should usually live in docs if they are explanatory.
- Example images should be small and directly tied to running/loading an example.
- Do not include screenshots containing private project data.

### 10.6 Weather/EPW files

- Require license, provenance, and size review.
- Prefer references or instructions over committing large weather files.
- Small synthetic or public-domain weather snippets may be considered only by explicit approval.

### 10.7 Material assets

- Extension runtime material assets should stay extension-local.
- General example material assets require license/provenance review.
- Do not duplicate setup extension assets into examples without a clear demo need.

## 11. Current Sample Classification

| Current path | Classification | Recommendation |
| --- | --- | --- |
| `source/extensions/custom.aec.thermal_viz/data/sample_temperature_day.csv` | extension-local sample telemetry | Stay extension-local for now. Future copy to `examples/telemetry/` only if it becomes a general tutorial input. |
| `source/extensions/custom.aec.sketch/data/icon.png` | extension metadata asset | Stay extension-local. Not a root example. |
| `source/extensions/custom.aec.sketch/data/preview.png` | extension preview/metadata asset | Stay extension-local. Not a root example. |
| `source/extensions/custom.aec.sketch/docs/README.md` | extension-local docs/template note | Stay extension-local for now; future docs review may replace template language. |
| `source/extensions/custom.aec.sketch/docs/Overview.md` | extension-local docs metadata | Stay extension-local. |
| `source/extensions/custom.aec.sketch/docs/CHANGELOG.md` | extension-local changelog | Stay extension-local. |
| `source/extensions/custom.aec.thermal_viz/README.md` | extension-local usage doc with telemetry examples | Stay extension-local; snippets may inform future `docs/examples` or `examples/telemetry`. |
| `source/extensions/my_company.my_usd_composer_setup_extension/data/stage_templates/zup_default_stage.py` | setup extension runtime asset | Stay extension-local. Not a root example unless a future tutorial needs a copy. |
| setup extension `data/BuiltInMaterials.usda` | setup/app material asset | Stay extension-local; no duplication into examples without license/provenance and demo need. |
| setup extension `data/flattener_materials/*.mdl` | setup/app material assets | Stay extension-local; vendor/template provenance should be preserved. |
| setup extension `layouts/default.json` | app/setup layout asset | Stay extension-local. Not a root example. |
| root `00_*.txt` to `07_*.txt` files | owner-decision planning/workflow notes | Owner review required; tutorial/example content may be extracted later into docs or examples. |
| `digital_twin_contexto_maestro.md` | strategic/master context | Owner review required; do not promote to public examples directly. |
| future EnergyPlus sample files | future example or fixture candidate | Require license, size, reproducibility, and runnable/illustrative decision. |
| future USD sample scenes | future root examples or test fixtures | Use synthetic small USDA; keep private geometry out. |
| `DT.xlsx` / `~$DT.xlsx` | unknown local spreadsheet artifacts | Owner review required; should not be treated as examples without classification. |

## 12. Examples and Tests Boundary

Examples demonstrate usage. Tests assert correctness.

Rules:

- examples may be smoke-testable
- examples should not replace tests
- tests may reuse tiny example inputs only when stable and intentional
- tests should not depend on tutorial prose
- examples may include expected behavior descriptions, but not as the only verification
- generated expected outputs belong in tests/snapshots only when approved

## 13. Examples and Docs Boundary

Docs explain. Examples run or load.

Rules:

- `docs/examples` should contain short explanatory snippets and links
- root `examples` should contain runnable/loadable artifacts
- tutorials may link to root examples
- docs should not duplicate large payloads
- example READMEs should explain local usage, while architecture docs define policy

## 14. Examples and Runtime Outputs Boundary

Rules:

- root examples may include input files and expected descriptions
- generated outputs go to future `runs/` or `outputs/`
- example outputs may be committed only if tiny, canonical, and explicitly approved
- examples must not include bulk simulation results
- examples must not write into their own source directories by default

## 15. Public and Private Policy

This repository is public. Examples must be safe to publish.

Rules:

- no private building data
- no real sensor data without anonymization and owner approval
- no proprietary assets without permission
- no licensed vendor examples without permission
- no private prompts, API keys, tokens, or credentials
- public-domain or synthetic data preferred
- provenance must be documented for nontrivial assets

## 16. Codex Access Policy for Examples

Codex may:

- create examples only when a ticket explicitly allows it
- inspect examples and extension-local data for classification
- add README/usage instructions when creating examples
- validate example paths and commands when possible

Codex must:

- keep examples small
- avoid private data
- avoid generated outputs
- avoid local absolute paths
- document dependencies and expected outputs
- avoid changing source/extensions while working on examples unless explicitly scoped

Codex must not:

- create `examples/` during architecture-only tickets
- move extension-local assets without explicit migration scope
- add large files
- add secrets
- add private building/sensor data
- commit generated simulation outputs
- duplicate vendor/template assets without license/provenance review

## 17. Open Decisions

Open decisions:

1. Whether root examples should be runnable from clean clone by default.
2. Whether some root examples should become smoke-test inputs.
3. Whether EnergyPlus examples should include real EPW/IDF files or only snippets/manifests.
4. Whether USD sample scenes should be committed now or after AEC schema conventions stabilize.
5. Exact artifact size limits for examples.
6. Whether screenshots belong under `examples/` or only under docs.
7. Whether end-to-end demos should live under `examples/demos/` or a separate future `demos/` folder.
8. Whether `sample_temperature_day.csv` should be copied into root examples or remain extension-local only.
9. Whether root owner-decision files contain tutorial content worth extracting.
10. How to classify `DT.xlsx` if it contains project/example data.

## 18. Risks

- Examples can become stale if they are not smoke-tested or linked to docs.
- Example assets can accidentally duplicate extension runtime assets.
- Large examples can make Git heavy and blur the line with datasets.
- Public examples can leak private building, sensor, or strategy data.
- EnergyPlus examples can create false expectations if they are illustrative but not runnable.
- Screenshots and visual examples can drift as UI changes.
- Root examples can be mistaken for tests unless their purpose is documented.
- Vendor/template assets may have licensing/provenance constraints.

## 19. Recommended Future Tickets

Recommended follow-up tickets:

1. Decide whether to create a minimal `examples/README.md` and initial folder skeleton.
2. Create a tiny synthetic telemetry example under future `examples/telemetry/`, if approved.
3. Design a minimal synthetic USD/USDA AEC scene under future `examples/usd/`.
4. Decide EnergyPlus example policy before adding IDF/EPW files.
5. Review root owner-decision files for tutorial/example content that should move to docs or examples.
6. Define example artifact size limits and provenance template.
