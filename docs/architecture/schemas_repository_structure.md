# Schemas Repository Structure Contract

Status: proposed architecture contract  
Scope: future root `schemas/` structure only  
Date: 2026-05-24

## 1. Executive Summary

This repository does not currently have a root-level `schemas/` directory. Shared contracts exist,
but they are embedded across Kit extension code and architecture docs:

- AEC USD conventions are documented in `docs/07_USD_MODELING_CONVENTIONS.md` and implemented
  through `aec:*` attributes/relationships in `custom.aec.modeling`.
- Partition and opening intent contracts are implemented in `partition_specs.py` and
  `opening_specs.py`.
- Thermal telemetry contracts are represented as Python dataclasses in `custom.aec.thermal_viz`.
- Agent actions, tool specifications, JSON-like input schemas, and tool result dictionaries are
  implemented in `dt.energy.agent`.
- Future backend run/output/data manifests are already discussed in architecture contracts, but
  no machine-readable schema exists yet.

Future root `schemas/` should contain shared, implementation-neutral data contracts that are used
across Kit extensions, future packages, backend services, tests, examples, AI tools, telemetry
flows, EnergyPlus workflows, and APIs. It should not contain runtime payloads, generated outputs,
private data, source implementation code, Kit app descriptors, or extension configuration.

This document is a design contract only. It does not create `schemas/`, generate schema files,
move code, edit source, run build/launch/tests, stage, commit, or push.

## 2. Current Schema and Contract Inventory

Current schema-like contracts are distributed:

| Area | Current location | Current contract form |
| --- | --- | --- |
| AEC USD layout | `docs/07_USD_MODELING_CONVENTIONS.md` | Markdown convention contract |
| AEC block/building metadata | `custom.aec.modeling/custom_aec/modeling/api.py` | USD `aec:*` attributes and relationships |
| Partition intent | `custom.aec.modeling/custom_aec/modeling/partition_specs.py` | USD prim/attribute convention plus Python dictionaries |
| Opening intent | `custom.aec.modeling/custom_aec/modeling/opening_specs.py` | USD prim/attribute convention plus Python dictionaries |
| AEC validation/readiness | `dt.energy.agent/tools/aec_inspection.py` | Tool result dictionaries over USD metadata |
| Thermal spaces | `custom.aec.thermal_viz/model_access.py` | `SpaceInfo` dataclass over USD metadata |
| Thermal telemetry series | `custom.aec.thermal_viz/timeseries.py` | `TelemetrySeries`, `ZoneTelemetryBinding`, mutable store |
| Telemetry datasets | `custom.aec.thermal_viz/data_sources.py` | `TelemetryDataset`, CSV/JSON shape assumptions |
| Thermal synthetic signals | `custom.aec.thermal_viz/signals.py` | `ThermalSignal` dataclass |
| Agent action | `dt.energy.agent/core/message_types.py` | `AgentAction` dataclass |
| Agent tool specs | `dt.energy.agent/tools/registry.py` | `ToolSpec` dataclass plus inline JSON Schema-like dicts |
| Agent tool schema export | `dt.energy.agent/mcp/tool_schema.py` | `TOOLS = tool_schemas()` |
| Agent tool result | `dt.energy.agent/tools/results.py` | common result dictionary: `ok`, `message`, `data`, `warnings`, `errors` |
| EnergyPlus placeholder export | `dt.energy.agent/tools/idf_tools.py` | placeholder IDF text generation and output metadata |
| EnergyPlus execution request | `dt.energy.agent/tools/simulation_tools.py` | disabled MVP request shape: `idf_path`, `weather_path` |
| Run/output/data manifests | architecture docs | conceptual JSON/TOML manifest contracts |

There is currently no canonical machine-readable schema registry. Several contracts are repeated
implicitly in code, docs, and tool return shapes.

## 3. Architectural Role of Future `schemas/`

Future root `schemas/` should be the home for shared data contracts when a payload or convention is
used across more than one architectural layer.

Use `schemas/` for:

- shared payload contracts between Kit, packages, backend, tests, examples, and AI tools
- stable JSON Schema files for request/response/result payloads
- OpenAPI files for future public or internal APIs
- metadata contracts for run, output, data, and validation manifests
- telemetry payload contracts
- EnergyPlus job/result contracts
- AI agent action/tool/result contracts
- USD metadata convention contracts when they need machine-readable validation or cross-layer use
- minimal valid/invalid schema examples

Do not use `schemas/` for:

- generated runtime payloads
- actual run manifests from real executions
- large datasets or telemetry dumps
- private building/sensor data
- secrets or local configuration
- binary outputs
- implementation code
- extension startup code
- `extension.toml`
- app `.kit` descriptors
- generated OpenAPI or generated code outputs unless explicitly approved
- notebooks

The short rule is: `schemas/` contains shared contracts, not implementations and not data.

## 4. Proposed Future Layout

When `schemas/` is eventually created by a future ticket, the recommended structure is:

```text
schemas/
  README.md
  aec/
  energy/
  energyplus/
  telemetry/
  results/
  ai_agent/
  api/
  usd/
  validation/
  examples/
```

### `schemas/README.md`

Index of available schemas, versioning policy, validation commands, compatibility notes, and links
to consuming packages/extensions/backend services.

### `schemas/aec/`

Contracts for AEC domain objects: buildings, blocks, spaces, surfaces, partitions, openings,
sketches, bounds, adjacency, construction metadata, and export readiness.

### `schemas/energy/`

Contracts for project-level energy model abstractions that are not EnergyPlus-specific: zones,
constructions, schedules, loads, HVAC placeholders, thermal properties, and model readiness.

### `schemas/energyplus/`

Contracts for EnergyPlus jobs and processed results: IDF export requests, EPW references,
simulation job manifests, executable/config references, processed outputs, and error summaries.
Raw IDF syntax itself should not be reinvented here.

### `schemas/telemetry/`

Contracts for telemetry datasets, time-series samples, sensor bindings, channels, units,
timestamps, timezones, sampling rates, and source metadata.

### `schemas/results/`

Shared result envelopes and status payloads used by tools, backend jobs, validations, and future
API responses. The current `tool_result()` dictionary is the first candidate.

### `schemas/ai_agent/`

Contracts for agent actions, tool specs, tool input schemas, confirmation/safety metadata, and
tool-call results.

### `schemas/api/`

Future OpenAPI or endpoint payload contracts. This folder should remain empty until backend/API
boundaries are real enough to justify it.

### `schemas/usd/`

Schema-like USD metadata conventions that describe `aec:*` attributes, relationships, prim
locations, allowed values, and version markers. These may be Markdown plus machine-readable
attribute tables if full USD schema generation is not justified.

### `schemas/validation/`

Validation meta-schemas, schema test definitions, compatibility checks, or validation rule
definitions. Executable validators should live in future `scripts/`, `packages/`, or tests.

### `schemas/examples/`

Tiny valid and invalid example payloads used to document schemas. Larger runnable examples belong
under future `examples/`. Assertion-oriented fixtures belong under future `tests/fixtures/`.

## 5. Supported Schema Formats

Recommended format policy:

| Format | Use | Location |
| --- | --- | --- |
| JSON Schema | Shared JSON-compatible payload contracts, manifests, telemetry, tool inputs/results | `schemas/` |
| OpenAPI | Future backend/API endpoint contracts | `schemas/api/` |
| Pydantic models | Typed runtime validation and ergonomic Python APIs | future `packages/`, not root `schemas/` |
| Dataclasses | Internal typed models where validation is light or runtime-local | packages/extensions/backend, not root `schemas/` |
| USD convention docs/tables | USD `aec:*` attributes, relationships, prim paths, allowed values | `schemas/usd/` or `docs/architecture` depending maturity |
| TOML/YAML config schemas | Future committed config contracts | `schemas/validation/` or future `config/` policy, depending scope |
| Markdown-only contracts | Human-readable conventions and rationale | `docs/`; may link to machine-readable schemas |

Root `schemas/` should prefer implementation-neutral formats. Python classes may implement schemas,
but the shared contract should not depend on importing Kit, backend, or package code.

## 6. Versioning Policy

Schemas should be versioned when they are consumed by more than one layer or when external data may
outlive a single commit.

Recommended policy:

- Include an explicit `schema_version` or equivalent version field in persisted payloads.
- Use semantic versioning for stable schemas: `1.0.0`, `1.1.0`, `2.0.0`.
- Use MVP labels only for temporary internal contracts, for example `mvp-1`, but migrate to
  semantic versions before public API or backend adoption.
- Treat required-field removal, type changes, enum value removal, and semantic meaning changes as
  breaking changes.
- Treat optional-field additions as non-breaking when consumers ignore unknown fields.
- Document migrations for breaking changes.
- Keep deprecated schemas until all known committed examples/tests/manifests have migrated.
- Do not silently change a schema consumed by Kit, backend, and tests in the same broad edit.

Schema identifiers should be stable and domain-scoped, for example:

- `dt.aec.block`
- `dt.aec.surface`
- `dt.telemetry.series`
- `dt.energyplus.job_request`
- `dt.results.tool_result`
- `dt.ai_agent.tool_spec`

## 7. Naming Conventions

Recommended naming:

- lowercase snake_case filenames
- domain subfolders
- explicit purpose in the filename
- optional version suffix only when multiple active versions must coexist
- no vague names such as `data.json`, `payload.json`, or `schema.json`

Example future names:

```text
schemas/aec/block.schema.json
schemas/aec/surface.schema.json
schemas/aec/opening_spec.schema.json
schemas/aec/partition_spec.schema.json
schemas/telemetry/series.schema.json
schemas/telemetry/zone_binding.schema.json
schemas/results/tool_result.schema.json
schemas/ai_agent/agent_action.schema.json
schemas/ai_agent/tool_spec.schema.json
schemas/energyplus/job_request.schema.json
schemas/energyplus/processed_result.schema.json
schemas/validation/run_manifest.schema.json
schemas/validation/output_metadata.schema.json
```

## 8. Schemas and Packages Relationship

Future packages may implement typed models around schemas.

Rules:

- Packages may load and validate against schemas.
- Packages may expose Pydantic/dataclass models that correspond to schemas.
- Schemas must not import packages.
- Generated Python code from schemas should not be committed unless explicitly approved.
- Avoid duplicating contract definitions in both package code and schema files without a clear
  source-of-truth rule.
- If Pydantic-first development is chosen later, generated JSON Schema should be reviewed before
  promotion to root `schemas/`.

Recommended source-of-truth pattern:

- Machine-readable shared payload contract: `schemas/`.
- Python implementation and validators: future `packages/`.
- Human rationale and architecture: `docs/architecture`.

## 9. Schemas and Backend Relationship

Future backend request/response payloads should use shared schemas when consumed by Kit, packages,
tests, examples, or external clients.

Rules:

- Backend job request payloads should validate at service boundaries.
- Backend job manifests should follow shared manifest schemas once defined.
- Backend result payloads should use shared result schemas.
- Backend must not define private duplicate contracts for payloads shared with Kit.
- Backend-specific internal task records may remain backend-local until shared.
- EnergyPlus subprocess configuration should use explicit schemas before real execution workflows
  become reusable.

## 10. Schemas and Kit Extensions Relationship

Kit extensions should use shared schemas/contracts for payloads that cross extension/package/backend
boundaries.

Rules:

- `extension.toml` is not part of root `schemas/`.
- App `.kit` descriptors are not part of root `schemas/`.
- USD stage metadata adapters may map USD state into schema/domain payloads.
- USD `aec:*` conventions may become machine-readable schema-like contracts under `schemas/usd/`
  if validation or backend export requires it.
- Kit UI extensions should not privately define durable backend/API payload shapes.
- Direct USD mutation should stay in Kit adapters; schema payloads should describe the domain state
  being exchanged.

## 11. Schemas, Tests, and Examples Relationship

Tests and examples should use schemas deliberately:

- Tests may validate valid/invalid payload fixtures against schemas.
- Future `tests/fixtures` may include tiny assertion-oriented payloads.
- `schemas/examples` may include minimal schema examples for documentation.
- Root `examples/` may contain runnable workflows that reference schemas.
- Examples should not become tests unless intentionally reused.
- Test snapshots should not be arbitrary generated outputs; they should be stable, small, and
  approved.

## 12. Schema Validation Workflow

Future validation should be introduced in phases:

1. Add a schema and minimal valid/invalid examples.
2. Add a read-only validation command, likely under future `scripts/validation/` or
   `scripts/repo_hygiene/`.
3. Add package/backend validators when the schema is consumed at runtime.
4. Add tests for compatibility and representative invalid payloads.
5. Add CI only after the local validation command is stable.

Codex-safe future validation commands should be read-only by default, for example:

```powershell
python scripts/validation/validate_schemas.py --dry-run
python scripts/repo_hygiene/check_schema_examples.py
```

No generated schema outputs, generated API clients, generated Python models, or validation reports
should be committed unless a ticket explicitly approves them.

## 13. Current Candidate Classification

| Candidate | Current location | Classification | Recommendation |
| --- | --- | --- | --- |
| AEC building/block/space/surface metadata | `docs/07_USD_MODELING_CONVENTIONS.md`, `custom.aec.modeling/api.py` | USD convention and domain contract | Future `schemas/usd/` and `schemas/aec/` candidates; keep extension-local for now |
| `aec:schemaVersion=mvp-1` | `api.py`, docs | Version marker | Future versioning policy candidate; do not change yet |
| Partition specs | `partition_specs.py` | USD metadata contract | Future `schemas/aec/partition_spec.schema.json`; needs tests first |
| Opening specs | `opening_specs.py` | USD metadata contract | Future `schemas/aec/opening_spec.schema.json`; needs tests first |
| Surface basis attributes | docs and rebuild/modeling code | USD convention | Future `schemas/usd/surface_metadata` candidate; docs convention for now |
| Energy readiness metadata | `api.py`, `thermal_sync_tools.py`, docs | Domain/energy contract | Future `schemas/energy/` candidate; keep extension-local for now |
| `SpaceInfo` | `custom.aec.thermal_viz/model_access.py` | Typed adapter model over USD | Future package typed model candidate; schema only if shared outside Kit |
| `TelemetrySeries` | `custom.aec.thermal_viz/timeseries.py` | Telemetry domain model | Future `schemas/telemetry/series.schema.json` and package typed model |
| `ZoneTelemetryBinding` | `timeseries.py` | Telemetry binding model | Future `schemas/telemetry/zone_binding.schema.json` |
| `TelemetryDataset` | `data_sources.py` | Dataset contract | Future `schemas/telemetry/dataset.schema.json`; needs sample validation |
| CSV/JSON telemetry shape | `data_sources.py`, sample CSV | File format convention | Future telemetry schema/docs candidate; examples should remain small |
| `ThermalSignal` | `signals.py` | Synthetic signal model | Future package typed model; schema only if persisted/shared |
| `AgentAction` | `message_types.py` | Agent action contract | Future `schemas/ai_agent/agent_action.schema.json` |
| `ToolSpec` | `tools/registry.py` | Agent tool contract | Future `schemas/ai_agent/tool_spec.schema.json`; current inline schemas can guide it |
| Inline tool input schemas | `tools/registry.py` | JSON Schema-like fragments | Future root schema candidates once tools stabilize |
| `tool_result()` | `tools/results.py` | Shared result envelope | Future `schemas/results/tool_result.schema.json`; high-value early candidate |
| IDF placeholder export summary | `idf_tools.py` | Export result shape | Future `schemas/energyplus/idf_export_result.schema.json` after tests |
| EnergyPlus job request | `simulation_tools.py`, registry `_simulation_schema()` | Disabled MVP request shape | Future `schemas/energyplus/job_request.schema.json`; backend-specific until real backend exists |
| Future backend job manifest | backend/runs docs | Manifest contract | Future `schemas/validation/` or `schemas/energyplus/` candidate |
| Future run/output/data manifests | runs/outputs/data docs | Manifest contracts | Future `schemas/validation/` candidates; no real payloads yet |

## 14. What Must Not Go Into `schemas/`

Root `schemas/` must not contain:

- generated runtime payloads
- real run manifests from local executions
- EnergyPlus output files
- generated IDFs from real projects
- telemetry dumps
- large datasets
- private building or sensor data
- secrets or credentials
- notebooks
- binary outputs
- implementation modules
- package source code
- backend service code
- Kit UI code
- `extension.toml`
- app `.kit` descriptors
- generated OpenAPI outputs unless approved
- generated code clients unless approved

## 15. Codex Access Policy

Codex may create or edit schemas only when a ticket explicitly allows schema changes.

Required behavior for future schema tasks:

- Inspect current domain models before proposing schemas.
- Do not invent schemas disconnected from current implementation or approved future contracts.
- Include minimal examples and validation notes when adding a schema.
- Do not expose private payloads or real user/building data as examples.
- Do not silently duplicate package/backend/extension contracts.
- Update relevant docs/tests when schema changes affect active contracts.
- Treat breaking schema changes as high-impact architecture changes.
- Do not run schema generators unless explicitly requested.
- Do not commit generated clients/models without approval.

## 16. Open Decisions

- Whether to introduce root `schemas/` before future `packages/`.
- Whether JSON Schema or Pydantic-first should be the primary authoring model.
- Whether schema versions should be semantic versions, date versions, or domain-specific labels.
- Whether USD `aec:*` conventions need machine-readable validation or can remain docs plus package validators.
- Whether agent tool schemas should remain inline until the agent boundary stabilizes.
- Whether backend APIs should use OpenAPI from the start or wait until API surface is real.
- Whether run/output/data manifests should share one base manifest schema.
- How to prevent schema drift between docs, Python dataclasses, JSON Schemas, and generated API docs.
- Whether schema examples belong under `schemas/examples` or beside each domain schema.

## 17. Risks

- Introducing schemas too early can freeze unstable MVP design.
- Delaying schemas too long can let Kit, backend, packages, tests, and AI tools drift apart.
- JSON Schema and Python typed models can diverge if source-of-truth is unclear.
- USD metadata is harder to validate than plain JSON payloads; schema contracts may become partial.
- Agent tool schemas are currently tied to callable implementation; moving them too soon could slow iteration.
- Public examples can accidentally expose private building, path, or telemetry data.
- Versioning creates compatibility burden once schemas are consumed by persisted files or external APIs.
- Backend/API work may duplicate contracts if schemas are not introduced deliberately.

## 18. Validation Commands Used for This Contract

Read-only commands used while preparing this document:

```powershell
git status --short
Test-Path schemas
Get-ChildItem source\extensions\custom.aec.modeling -Recurse -File -Force | Select-Object FullName,Length
Get-ChildItem source\extensions\custom.aec.thermal_viz -Recurse -File -Force | Select-Object FullName,Length
Get-ChildItem source\extensions\dt.energy.agent -Recurse -File -Force | Select-Object FullName,Length
rg -n "schema|contract|payload|message|result|metadata|ToolSpec|dataclass|TypedDict|Pydantic|BaseModel|json_schema|OpenAPI|manifest|telemetry|zone|space|surface|idf" docs source README.md
Get-Content source\extensions\custom.aec.modeling\custom_aec\modeling\opening_specs.py
Get-Content source\extensions\custom.aec.modeling\custom_aec\modeling\partition_specs.py
Get-Content source\extensions\dt.energy.agent\dt\energy\agent\core\message_types.py
Get-Content source\extensions\dt.energy.agent\dt\energy\agent\mcp\tool_schema.py
Get-Content source\extensions\dt.energy.agent\dt\energy\agent\tools\registry.py
Get-Content source\extensions\dt.energy.agent\dt\energy\agent\tools\results.py
Get-Content source\extensions\custom.aec.thermal_viz\custom_aec\thermal_viz\timeseries.py
Get-Content source\extensions\custom.aec.thermal_viz\custom_aec\thermal_viz\data_sources.py
Get-Content source\extensions\custom.aec.thermal_viz\custom_aec\thermal_viz\signals.py
Get-Content docs\07_USD_MODELING_CONVENTIONS.md
Get-Content source\extensions\dt.energy.agent\dt\energy\agent\tools\idf_tools.py
Get-Content source\extensions\dt.energy.agent\dt\energy\agent\tools\simulation_tools.py
Get-Content source\extensions\custom.aec.thermal_viz\custom_aec\thermal_viz\model_access.py
Get-Content source\extensions\custom.aec.modeling\custom_aec\modeling\api.py | Select-Object -First 220
```

## 19. Recommended Next Ticket

Recommended next ticket: design the future `config/` repository structure, because schema policy
and configuration policy intersect around backend job requests, local EnergyPlus settings, runtime
manifests, and validation commands.
