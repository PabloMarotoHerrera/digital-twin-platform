# Backend Repository Structure Contract

Status: proposed architecture contract  
Scope: future `backend/` structure only  
Date: 2026-05-24  

## 1. Purpose

This document defines the intended future `backend/` structure for headless services, process
orchestration, EnergyPlus execution, batch simulation, calibration, dataset generation, surrogate
training, and future control/RL workflows.

This is a design contract only. It does not create `backend/`, run EnergyPlus, move code, edit source,
change Kit integration, stage, commit, or push.

The current reproducible baseline remains an NVIDIA Omniverse Kit App Template derivative. The active
Kit-integrated source-of-truth remains:

```text
source/apps/
source/extensions/
```

Future reusable Python libraries belong under `packages/`. Future service/process orchestration
belongs under `backend/`.

## 2. Current State Observed

There is currently no `backend/` directory in this working copy.

The current backend-like behavior is still inside Kit extensions:

```text
source/extensions/dt.energy.agent/dt/energy/agent/tools/simulation_tools.py
source/extensions/dt.energy.agent/dt/energy/agent/tools/idf_tools.py
source/extensions/dt.energy.agent/dt/energy/agent/tools/thermal_tools.py
source/extensions/dt.energy.agent/dt/energy/agent/tools/thermal_sync_tools.py
source/extensions/custom.aec.thermal_viz/custom_aec/thermal_viz/data_sources.py
source/extensions/custom.aec.thermal_viz/custom_aec/thermal_viz/mqtt_client.py
```

Observed facts:

- `run_energyplus()` is currently a disabled placeholder and explicitly reports that EnergyPlus is not
  connected.
- `export_idf_placeholder()` writes a structured placeholder IDF from the current Kit stage and uses
  `omni.usd`, `carb`, and stage inspection helpers.
- The current default IDF output path is `C:/temp/energy_model.idf`.
- Existing path safety logic allows only `C:/temp` and `C:/tmp` for some agent outputs.
- Thermal sync tools are USD/Kit-bound and mutate the stage.
- Thermal telemetry data sources are mostly headless file parsing and synthetic data generation.
- The MQTT client is a socket/thread based runtime client currently owned by the thermal visualization
  extension.
- No `EnergyPlusV24-2-0` directory exists in this working copy at the time of this ticket.
- Local spreadsheet artifacts `DT.xlsx` and `~$DT.xlsx` are present as untracked owner-decision files;
  they are not backend source and are not touched by this contract.

## 3. Architectural Role of `backend/`

Future `backend/` should contain headless workflow orchestration that is larger than a library and
should not run inside a Kit UI extension.

Suitable backend responsibilities:

- launching and supervising EnergyPlus runs
- managing simulation job directories
- validating simulation inputs before execution
- batch simulation workflows
- calibration loops
- synthetic dataset generation workflows
- surrogate training and inference service orchestration
- control and RL experiment orchestration
- worker processes
- local API service endpoints
- job status tracking
- integration with external compute, containers, or HPC when needed

`backend/` should be service/process-oriented. It may start as local-first Python orchestration, but
its boundaries should not prevent future worker queues, containers, or distributed execution.

## 4. What Belongs in `backend/`

Acceptable future backend content:

- service entrypoints
- worker entrypoints
- process orchestration code
- EnergyPlus executable invocation wrappers
- job lifecycle management
- backend configuration loaders
- API route handlers
- local service adapters
- queue workers
- batch simulation workflows
- calibration orchestration
- dataset generation orchestration
- surrogate training pipelines
- control/RL experiment runners
- integration tests for external executables or services
- backend-specific docs after backend exists

## 5. What Does Not Belong in `backend/`

Do not place these in `backend/`:

- Kit UI code
- `omni.ext.IExt` startup classes
- `extension.toml` files
- app `.kit` descriptors
- extension icons, previews, or Kit registry assets
- pure reusable algorithms that belong in `packages/`
- one-off developer scripts that belong in future `scripts/`
- shared schemas that belong in future `schemas/`
- runtime outputs
- generated IDF files, ESO files, CSV results, or EnergyPlus run folders
- large generated datasets
- trained model binaries/checkpoints
- notebooks
- vendor binaries unless explicitly approved
- secrets
- user-level Omniverse config
- generated build artifacts
- pycache or bytecode

## 6. Difference From Other Repository Areas

### 6.1 `backend/` vs `packages/`

`packages/` contains reusable libraries: models, validators, parsers, algorithms, and public APIs.

`backend/` orchestrates workflows and processes. It may depend on packages, but packages must not
depend on backend.

Examples:

- `dt_energyplus` package: IDF builder and output parser.
- `backend/energyplus`: configured executable runner, job directories, subprocess lifecycle, and
  execution policy.

### 6.2 `backend/` vs `source/extensions/`

`source/extensions/` owns Kit integration: UI, stage adapters, `extension.toml`, menus, commands, and
extension startup.

`backend/` owns headless execution. It should not import UI extension internals. Kit should call
backend through explicit commands, service APIs, adapter clients, or well-defined files/contracts.

### 6.3 `backend/` vs `scripts/`

`scripts/` should contain small developer or automation entrypoints.

`backend/` should contain durable orchestration code with tests, configuration, job lifecycle rules,
and service boundaries.

### 6.4 `backend/` vs `runs/`, `outputs/`, and `data/`

`backend/` is source code. It must not contain run outputs.

Future runtime/artifact destinations:

- `runs/`: local simulation/job run directories.
- `outputs/`: generated reports, exports, and processed outputs.
- `data/`: curated input datasets or small fixtures, subject to size and public/private policy.
- artifact store: large datasets, trained models, checkpoints, and long-running results.

These folders are future concepts and are not created by this ticket.

## 7. Proposed Future Backend Layout

Recommended future structure:

```text
backend/
  README.md
  pyproject.toml
  backend_app/
    __init__.py
    energyplus/
    simulation/
    calibration/
    dataset_generation/
    surrogates/
    control/
    rl/
    workers/
    api/
    config/
  tests/
  docs/
```

Exact package naming is open. `backend_app` is a placeholder namespace, not a final decision.

## 8. Backend Subdomains

### 8.1 `backend/energyplus/`

Purpose: EnergyPlus executable integration and run management.

Responsibilities:

- locate and validate EnergyPlus executable
- validate IDF and EPW paths
- create isolated run directories
- invoke EnergyPlus through a locked-down subprocess wrapper
- capture stdout/stderr/log files
- parse exit codes
- enforce timeouts and cancellation
- return normalized result objects

Allowed dependencies:

- `packages/dt_core`
- `packages/dt_energy`
- `packages/dt_energyplus`
- `packages/dt_results`
- Python subprocess/path libraries

Forbidden dependencies:

- Kit UI
- `source/extensions` internals
- hardcoded machine-specific paths
- arbitrary shell command execution
- direct writes into backend source directories

Runtime outputs location:

- future `runs/energyplus/<run_id>/`
- future `outputs/energyplus/` only for promoted reports or exports

Service/process orientation:

- local-first initially
- should remain compatible with future container or remote service execution

### 8.2 `backend/simulation/`

Purpose: general simulation workflow orchestration across model export, run execution, and result
collection.

Responsibilities:

- compose simulation jobs
- coordinate IDF generation, weather selection, run execution, and result parsing
- provide job status
- normalize simulation outputs
- support single-run and batch-run workflows

Allowed dependencies:

- `dt_core`
- `dt_aec`
- `dt_energy`
- `dt_energyplus`
- `dt_results`

Forbidden dependencies:

- Kit UI
- hidden stage mutation
- extension-private modules

Runtime outputs location:

- future `runs/simulation/<job_id>/`

Orientation:

- local-first, future worker-ready

### 8.3 `backend/calibration/`

Purpose: calibrate energy models against measured or synthetic telemetry.

Responsibilities:

- define calibration jobs
- coordinate parameter sweeps or optimizers
- compare simulation results with telemetry
- store calibration metrics
- produce calibrated parameter sets

Allowed dependencies:

- `dt_core`
- `dt_energy`
- `dt_results`
- `dt_sensors`
- approved optimization libraries after decision

Forbidden dependencies:

- Kit UI
- notebooks as primary workflow
- raw unbounded writes into repo

Runtime outputs location:

- future `runs/calibration/<job_id>/`
- promoted summaries under future `outputs/calibration/`

Orientation:

- local-first for MVP
- future distributed/HPC-ready for large sweeps

### 8.4 `backend/dataset_generation/`

Purpose: generate reproducible synthetic datasets from parameterized simulations.

Responsibilities:

- define sampling plans
- run batches
- normalize outputs
- produce dataset manifests
- track provenance
- validate dataset completeness

Allowed dependencies:

- `dt_core`
- `dt_energy`
- `dt_energyplus`
- `dt_results`
- `dt_sensors`

Forbidden dependencies:

- committing large generated datasets to Git by default
- Kit UI
- local-only absolute paths

Runtime outputs location:

- future `runs/dataset_generation/<job_id>/`
- future artifact store or `data/` only for approved small curated datasets

Orientation:

- future distributed/HPC-ready

### 8.5 `backend/surrogates/`

Purpose: train, evaluate, and serve surrogate models for energy behavior.

Responsibilities:

- training orchestration
- evaluation jobs
- model registry metadata
- inference service adapter if needed
- export formats such as ONNX only after approval

Allowed dependencies:

- `dt_core`
- `dt_results`
- approved ML libraries after decision

Forbidden dependencies:

- storing large checkpoints in Git by default
- Kit UI
- hardcoded GPU assumptions

Runtime outputs location:

- future `runs/surrogates/<job_id>/`
- external artifact store for checkpoints/models

Orientation:

- local-first for experiments
- future GPU/distributed-ready

### 8.6 `backend/control/`

Purpose: non-RL control workflows such as rule-based, optimization, MPC, or recommendation control.

Responsibilities:

- define control problem contracts
- evaluate policies
- coordinate simulation-based control experiments
- emit recommended actions
- enforce safety constraints

Allowed dependencies:

- `dt_core`
- `dt_energy`
- `dt_results`
- `dt_sensors`
- surrogate APIs after approval

Forbidden dependencies:

- direct mutation of a live Kit stage
- unbounded control actions without safety validation
- secrets or live building credentials

Runtime outputs location:

- future `runs/control/<job_id>/`

Orientation:

- local-first, future service-ready

### 8.7 `backend/rl/`

Purpose: reinforcement learning experiment orchestration for energy control.

Responsibilities:

- environment runner orchestration
- offline RL dataset use
- policy evaluation
- experiment tracking metadata

Allowed dependencies:

- `dt_core`
- `dt_results`
- `dt_energy`
- approved RL/ML libraries after decision

Forbidden dependencies:

- storing large checkpoints in Git
- live building actuation without explicit safety policy
- Kit UI

Runtime outputs location:

- future `runs/rl/<job_id>/`
- external artifact store for models

Orientation:

- research-first, future distributed/GPU-ready

### 8.8 `backend/workers/`

Purpose: worker process entrypoints for asynchronous or long-running jobs.

Responsibilities:

- execute queued jobs
- report status
- handle cancellation
- enforce resource/time limits
- isolate external process calls

Allowed dependencies:

- backend subdomains
- package APIs
- selected queue/runtime library after decision

Forbidden dependencies:

- Kit UI
- arbitrary shell execution
- direct user-provided command strings

Runtime outputs location:

- job-specific future `runs/<domain>/<job_id>/`

Orientation:

- optional until local synchronous orchestration becomes insufficient

### 8.9 `backend/api/`

Purpose: explicit service/API boundary for Kit, scripts, or external clients.

Responsibilities:

- expose simulation/job endpoints
- validate requests
- return result objects and job status
- handle authentication only after deployment decisions

Allowed dependencies:

- backend services
- packages
- selected framework such as FastAPI only after decision

Forbidden dependencies:

- Kit UI
- direct stage mutation
- long blocking work inside request handlers

Runtime outputs location:

- none directly; APIs create jobs under future `runs/`

Orientation:

- should not be over-engineered before local workflow proves the boundary

### 8.10 `backend/config/`

Purpose: committed examples and configuration schema/loading code.

Responsibilities:

- define config models
- load environment variables
- validate local paths
- provide example config templates

Allowed dependencies:

- `dt_core`
- config parsing libraries after decision

Forbidden dependencies:

- secrets
- machine-specific absolute paths in committed defaults
- private credentials

Runtime outputs location:

- none

Orientation:

- local-first with future deployment compatibility

### 8.11 `backend/tests/`

Purpose: backend-specific unit and integration tests.

Responsibilities:

- test orchestration logic
- test path safety
- test config loading
- test EnergyPlus wrapper behavior with fake executables
- mark real EnergyPlus tests as integration/slow

Allowed dependencies:

- backend modules
- packages
- small fixtures

Forbidden dependencies:

- long simulations in fast test suite
- real external services unless explicitly marked
- writes outside test temp directories

### 8.12 `backend/docs/`

Purpose: backend-local implementation documentation after backend exists.

Responsibilities:

- local service runbook
- worker operation notes
- EnergyPlus integration notes
- troubleshooting

Project-wide architecture should remain under `docs/architecture/`.

## 9. EnergyPlus Backend Boundary

EnergyPlus is a solver backend, not the platform's internal model.

Policy:

- model semantics should live in packages such as `dt_aec` and `dt_energy`
- IDF document construction should live in a future `dt_energyplus` package
- EnergyPlus executable invocation should live in `backend/energyplus`
- Kit extensions should gather or export model data through adapters, not run long EnergyPlus jobs
  directly

### 9.1 Executable configuration

EnergyPlus executable path should come from:

- environment variable, for example `ENERGYPLUS_EXE`
- local ignored config file
- committed example config with placeholder paths
- future service/container configuration

Committed config must not contain machine-specific absolute paths.

### 9.2 IDF export

IDF export has two layers:

- package layer: build IDF text/files from validated domain models
- adapter/backend layer: choose output path, write files, attach provenance, manage job directory

Current `export_idf_placeholder()` should remain in the extension for now. Future extraction should
move the pure IDF string builder into `dt_energyplus` and keep Kit stage collection in an extension
adapter.

### 9.3 EPW/weather inputs

Weather files should not be buried inside backend source.

Future policy:

- small public fixture EPWs may be committed only if license and size allow
- local weather files should be referenced by config or selected per job
- large weather libraries should live outside Git or in an artifact store
- weather file paths must be validated before execution

### 9.4 Simulation runs and outputs

EnergyPlus run directories should be isolated:

```text
runs/energyplus/<run_id>/
  input.idf
  weather.epw
  stdout.log
  stderr.log
  eplusout.err
  eplusout.eso
  eplusout.csv
  manifest.json
```

These outputs are runtime artifacts and should be gitignored by default. A small curated output may
be promoted as a test fixture only through explicit approval.

### 9.5 Local executable vs service vs container

Initial backend should be local-first:

- run a configured local EnergyPlus executable
- write to a controlled local run directory
- return normalized results

Future options:

- containerized EnergyPlus
- remote EnergyPlus service
- worker queue
- HPC/batch scheduler
- NVIDIA Air or other remote simulation environments if they become relevant

Do not design the MVP as distributed infrastructure before local execution is validated.

### 9.6 Security and sandboxing

EnergyPlus execution must:

- avoid arbitrary shell command strings
- use argument arrays rather than shell interpolation
- validate executable, IDF, EPW, and output paths
- restrict outputs to approved run directories
- prevent path traversal
- enforce timeouts
- support cancellation
- capture logs
- avoid reading secrets from model files

## 10. Backend and Packages Relationship

Rules:

- backend may depend on packages
- packages must not depend on backend
- backend orchestrates processes and workflows
- packages define reusable models, validation, parsers, and algorithms
- backend should use package public APIs instead of reaching into `source/extensions`
- backend should not duplicate package domain logic
- backend results should use package-defined result objects where possible

## 11. Backend and Kit Relationship

Rules:

- Kit extensions should not directly own long-running backend workloads.
- Kit should call backend via explicit commands, services, adapter clients, or files.
- backend must not import UI extension internals.
- shared contracts should go through packages or future schemas.
- backend should return explicit result objects or files, not hidden stage mutation.
- Kit adapters may import backend clients, but backend core must not import Kit UI.
- stage mutation after backend results should be a deliberate Kit adapter step.

Recommended future flow:

```text
Kit extension
  -> collect/export domain model through package/schema contract
  -> submit backend job
  -> backend runs EnergyPlus or batch workflow
  -> backend returns result object/output manifest
  -> Kit extension visualizes or imports results deliberately
```

## 12. Runtime and Output Policy

Backend source directories must stay clean.

Rules:

- no backend outputs under `backend/`
- simulation runs go to future `runs/`
- generated exports/reports go to future `outputs/`
- generated datasets go to future `data/` only if curated and small; otherwise artifact store
- trained models/checkpoints go to future model artifact storage, not Git by default
- logs go to runtime log folders, not source
- generated IDFs/results are not source-of-truth unless explicitly promoted as fixtures
- run manifests should record commit, package versions, config, input hashes, and timestamps

## 13. Backend Configuration Policy

Configuration policy:

- commit example config only, such as `.env.example` or `config.example.toml`
- keep real local config ignored
- no secrets in repo
- no private tokens in config
- no machine-specific absolute paths in committed defaults
- prefer environment variables for local executable paths and secrets
- validate config at startup
- define future config schemas for job requests and executable settings

EnergyPlus-related config:

- `ENERGYPLUS_EXE` or equivalent for executable path
- weather root path configured locally
- default run root configured locally or by repo policy
- no committed `C:/Users/...` paths
- no assumption that EnergyPlus is vendored in the repo

## 14. Backend Testing Policy

Backend tests should be split into fast and integration layers.

Fast tests:

- config parsing
- path validation
- command construction without execution
- job manifest creation
- fake EnergyPlus process wrapper
- IDF builder behavior through package APIs
- result parsing using small fixtures

Integration tests:

- real EnergyPlus executable discovery
- real short simulation
- file output validation
- service/API smoke tests

Rules:

- real EnergyPlus tests must be marked integration/slow
- tests must write only to temp directories
- no long simulations in default test suite
- fixtures must be small and license-safe
- tests should be reproducible from clean clone when optional dependencies are available
- Codex-safe validation should default to fast tests unless the ticket explicitly allows integration
  runs

## 15. Backend Security and Safety Policy

Backend code must treat external execution and user-provided paths as high-risk.

Rules:

- require explicit confirmation for subprocess execution in interactive workflows
- never execute arbitrary shell command strings from user input
- pass subprocess arguments as lists
- validate executable paths
- validate input file extensions and existence
- restrict output directories
- prevent path traversal
- enforce timeouts and resource limits
- support cancellation for long-running jobs
- capture stdout/stderr without flooding UI
- avoid logging secrets
- validate IDF/EPW paths before use
- treat downloaded or user-provided files as untrusted

## 16. Future Service/API Policy

The backend should start local-first unless a concrete workflow requires a service.

Acceptable future service options:

- local Python service
- FastAPI HTTP service
- gRPC service
- local worker queue
- batch/HPC execution adapter
- containerized EnergyPlus runner
- remote simulation service

Avoid over-engineering early:

- do not introduce API servers before a local backend workflow exists
- do not introduce queues before job duration/concurrency requires them
- do not introduce distributed execution before local reproducibility is stable
- do not expose public APIs before contracts and security are defined

## 17. Current Backend Candidate Classification

| Current/future area | Recommendation | Future target | Notes |
| --- | --- | --- | --- |
| `dt.energy.agent.tools.simulation_tools.run_energyplus` | Stay in extension for now; future backend candidate | `backend/energyplus` plus package result models | Currently disabled placeholder. Real subprocess execution belongs in backend, not Kit UI. |
| EnergyPlus placeholder runner | Future backend candidate; needs design first | `backend/energyplus` | Must validate executable, inputs, outputs, timeouts, cancellation, and logs. |
| `dt.energy.agent.tools.idf_tools.export_idf_placeholder` | Split later | `dt_energyplus` package plus Kit adapter/backend writer | Stage inventory is Kit-bound; `_build_placeholder_idf` is package-suitable. |
| IDF placeholder exporter | Future package/backend split; needs tests first | `dt_energyplus` and `backend/simulation` | Backend should manage job output path and manifest; package should build IDF content. |
| `dt.energy.agent.tools.thermal_tools` | Stay in extension for now | package/domain later | Thin wrapper around AEC validation/metadata tools; not backend yet. |
| `dt.energy.agent.tools.thermal_sync_tools` | Stay in extension | Kit adapter | Mutates USD stage and relies on `omni.usd`, `pxr`, and `custom_aec.modeling.api`. |
| `custom_aec.thermal_viz.data_sources` | Future package candidate before backend | `dt_sensors` | File parsing and synthetic telemetry are reusable library concerns. Backend may use package later. |
| `custom_aec.thermal_viz.mqtt_client` | Future package or backend/service candidate; needs review | `dt_sensors` or backend ingestion service | Runtime socket/thread lifecycle may belong in backend if ingestion becomes service-owned. |
| Telemetry ingestion | Future split candidate | `dt_sensors` plus `backend/workers` if long-running | Models/parsing in package; service lifecycle in backend. |
| Future calibration loops | Future backend candidate | `backend/calibration` | Requires package models, results, telemetry contracts, and test data policy first. |
| Future dataset generation | Future backend candidate | `backend/dataset_generation` | Must avoid committing generated datasets by default. |
| Future surrogate training | Future backend/service candidate | `backend/surrogates` | Models/checkpoints belong in artifact storage, not Git. |
| Future RL/control workflows | Future backend/service candidate | `backend/control`, `backend/rl` | Requires safety policy, simulation environment contract, and output storage policy. |
| Kit UI chat window and extension startup | Should not move to backend | Stay in `source/extensions` | UI and extension lifecycle remain Kit-owned. |
| Agent tool registry callable bindings | Stay in extension for now; future split | `dt_ai` package plus backend/Kit adapters | Tool schemas may become shared contracts; concrete Kit tool callables stay adapter-side. |

## 18. Codex Access Policy for Future `backend/`

Codex may:

- edit backend code when a ticket explicitly targets backend
- add backend tests for backend changes
- inspect Kit extensions to understand backend adapters
- document backend workflows and validation results

Codex must:

- run fast backend tests when modifying backend code
- mark slow/integration tests clearly
- use safe output directories
- avoid long simulations unless explicitly requested
- avoid EnergyPlus execution unless the ticket explicitly permits it
- preserve package and Kit boundaries
- report any generated runtime output paths

Codex must not:

- create `backend/` during architecture-only tickets
- execute arbitrary shell commands as backend simulation
- run broad cleanup commands
- modify Kit extensions while working on backend unless explicitly scoped
- commit generated run outputs
- add secrets, local machine paths, or private configs
- silently vendor EnergyPlus binaries

## 19. Open Decisions

Open backend decisions:

1. Backend framework choice: plain Python CLI, FastAPI, gRPC, worker queue, or phased combination.
2. Local process versus always-on service architecture.
3. EnergyPlus executable management: local install, external tool path, container, or remote service.
4. Whether EnergyPlus binaries should ever be vendored in-repo.
5. Weather/input file policy and storage location.
6. Run output storage: filesystem only, database metadata, artifact store, or hybrid.
7. Job queue design and whether it is needed before batch workloads.
8. HPC/distributed execution requirements.
9. Calibration result storage and comparison workflow.
10. Dataset artifact management and public/private dataset policy.
11. Model checkpoint/artifact management for surrogate and RL work.
12. API authentication and authorization if backend becomes network-accessible.
13. Whether MQTT ingestion belongs in backend service, package, or Kit extension for the next phase.
14. Whether `DT.xlsx` is project data, planning material, or unrelated local artifact.

## 20. Risks

- Running EnergyPlus from Kit UI can freeze or destabilize the interactive app if not moved behind a
  backend/process boundary.
- Hardcoded paths such as `C:/temp/energy_model.idf` are acceptable MVP placeholders but not a
  scalable backend policy.
- Subprocess execution introduces security risk without strict path and command validation.
- Generated simulation outputs can quickly pollute the repository if `runs/` and `outputs/` policy is
  not defined before real execution.
- Large datasets and trained models can make Git unusable if committed directly.
- Backend/package/extension boundaries may blur if extraction happens before package APIs and schemas
  are defined.
- Public repository status creates privacy risk for datasets, weather files, calibration data, and
  building-specific inputs.
- Service architecture can be over-engineered before the local EnergyPlus workflow is proven.

## 21. Recommended Future Tickets

Recommended follow-up tickets:

1. Decide backend MVP architecture: local CLI/process wrapper versus local service.
2. Define `runs/`, `outputs/`, `data/`, and artifact storage policy before running simulations.
3. Define EnergyPlus executable/config policy, including `.env.example` and ignored local config.
4. Add tests around the current IDF placeholder builder before extraction.
5. Extract pure IDF builder logic into a future `dt_energyplus` package after package policy is
   accepted.
6. Design a safe EnergyPlus subprocess wrapper with fake-executable tests before any real run.
7. Decide whether telemetry/MQTT ingestion remains Kit-owned or becomes backend service-owned.
