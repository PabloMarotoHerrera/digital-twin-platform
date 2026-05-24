# Runs Repository Structure Contract

Status: proposed architecture contract  
Scope: future root `runs/` structure only  
Date: 2026-05-24  

## 1. Purpose

This document defines the intended future root-level `runs/` structure for local runtime execution
directories produced by simulations, EnergyPlus jobs, calibration runs, dataset generation jobs,
surrogate training runs, RL/control experiments, backend jobs, smoke workflows, and validation
workflows.

This is a design contract only. It does not create `runs/`, generate run outputs, run EnergyPlus, run
simulations, edit source, update `.gitignore`, stage, commit, or push.

The repository is public, so runtime artifacts must be treated as local-only and high-risk for
accidental commits.

## 2. Current Runtime State Observed

There is currently no root-level `runs/` directory and no root-level `outputs/` directory.

Current runtime/generated/tooling-like folders at the repository root:

```text
_build/
_compiler/
_repo/
```

Observed details:

- `_build/` contains Kit-generated build/prebuild state, dependency material, generated app/test
  scripts, generated metadata, and release/debug build directories.
- `_repo/` contains Kit repo-tool dependency/cache state and `repo.log`.
- `_compiler/` contains compiler/toolchain link state.
- `git ls-files _build _repo _compiler` returned no tracked files.
- Code currently references `C:/temp` and `C:/tmp` as allowed output roots for MVP agent outputs.
- `dt.energy.agent.tools.simulation_tools.run_energyplus()` is currently disabled and does not run
  EnergyPlus.
- `dt.energy.agent.tools.idf_tools.export_idf_placeholder()` defaults to `C:/temp/energy_model.idf`.

These existing folders and paths are not root `runs/`. They are either Kit-managed generated/tooling
state or MVP local-output placeholders.

## 3. Architectural Role of Future Root `runs/`

Future root `runs/` should contain local execution directories created by controlled workflows.

Suitable `runs/` content:

- one directory per EnergyPlus execution
- one directory per backend simulation job
- one directory per calibration run
- one directory per dataset generation job
- one directory per surrogate training run
- one directory per control/RL experiment
- one directory per smoke/validation execution when artifacts are needed
- temporary scratch run directories that are explicitly local-only

`runs/` is for raw execution state. It is not source-of-truth and should be ignored by Git by default.

## 4. What Does Not Belong in `runs/`

Do not place these in `runs/`:

- source code
- reusable curated datasets
- public examples
- canonical docs
- package source
- backend source
- extension source
- long-term model artifacts
- vendor binaries
- EnergyPlus installation folders
- secrets
- credentials
- private data intended for public commit
- manually edited source-of-truth files
- permanent reports intended for publication

## 5. Difference From Related Areas

### 5.1 `runs/` vs `outputs/`

`runs/` contains raw execution directories. `outputs/` should contain promoted generated deliverables:
reports, exports, summaries, cleaned result files, or publication-ready artifacts.

Not every run produces an output worth keeping. Outputs should be selected and promoted deliberately.

### 5.2 `runs/` vs `data/`

`data/` contains curated input/source datasets. `runs/` consumes data and may generate candidate
datasets.

Generated datasets do not become `data/` automatically. Promotion to `data/` requires approval,
metadata, provenance, privacy review, and size review.

### 5.3 `runs/` vs `examples/`

`examples/` contains small runnable/loadable demonstration inputs and workflows. `runs/` contains
local execution results.

Examples may write to `runs/`, but examples should not store generated results inside their own source
directories.

### 5.4 `runs/` vs `tests/fixtures/`

`tests/fixtures/` contains tiny stable files used for assertions. `runs/` contains execution state and
may be large, private, or nondeterministic.

Tests may create temporary run directories, but should not depend on persistent root `runs/` by
default.

### 5.5 `runs/` vs `_build/`, `_repo/`, and `_compiler/`

`_build`, `_repo`, and `_compiler` are Kit-managed generated/tooling folders used by the App Template
workflow.

`runs/` is product/runtime workflow state owned by future backend/simulation workflows.

They should remain separate:

- do not put backend simulation runs under `_build`
- do not put Kit dependency caches under `runs`
- do not manually edit Kit-generated folders as run records

## 6. Proposed Future Root Layout

Recommended future layout:

```text
runs/
  README.md
  energyplus/
  simulation/
  calibration/
  dataset_generation/
  surrogates/
  control/
  rl/
  smoke/
  validation/
  tmp/
```

This ticket does not create these folders. If `runs/` is created later, it should be ignored by
default. A `.gitkeep` should be used only if the team explicitly wants the empty folder committed.

## 7. Run Category Policy

### 7.1 `runs/energyplus/`

Purpose: per-run EnergyPlus execution directories.

Owner: future backend EnergyPlus runner.

Typical contents:

- manifest
- generated or copied IDF
- EPW reference or approved copy
- stdout/stderr logs
- `eplusout.err`
- `eplusout.eso`
- `eplusout.csv`
- `eplusout.sql`
- status files
- parsed summary

### 7.2 `runs/simulation/`

Purpose: general simulation workflow runs that may involve export, solver execution, parsing, and
post-processing.

Owner: future backend simulation domain.

Typical contents:

- job manifest
- input references
- intermediate exports
- solver subdirectories
- result summaries
- workflow logs

### 7.3 `runs/calibration/`

Purpose: calibration runs against telemetry or benchmark data.

Owner: future backend calibration domain.

Typical contents:

- parameter sweep config
- iteration manifests
- metrics
- intermediate simulation runs
- calibration summaries
- temporary optimizer state

### 7.4 `runs/dataset_generation/`

Purpose: dataset generation jobs from batch simulation or synthetic data workflows.

Owner: future backend dataset-generation domain.

Typical contents:

- sampling plan
- batch manifest
- generated candidate dataset shards
- quality reports
- provenance summaries

Generated datasets remain run artifacts until promoted to `data/` or external artifact storage.

### 7.5 `runs/surrogates/`

Purpose: surrogate training/evaluation runs.

Owner: future backend surrogate domain.

Typical contents:

- training config
- metrics
- logs
- temporary checkpoints
- evaluation summaries
- TensorBoard or similar logs if used

Long-term model artifacts should be promoted to artifact storage, not committed from `runs/`.

### 7.6 `runs/control/`

Purpose: control workflow experiments such as rule-based control, MPC, or optimization.

Owner: future backend control domain.

Typical contents:

- control scenario config
- simulated action traces
- objective metrics
- safety constraint logs
- result summaries

### 7.7 `runs/rl/`

Purpose: reinforcement-learning experiments.

Owner: future backend RL domain.

Typical contents:

- environment config
- training metrics
- replay/evaluation summaries
- temporary checkpoints
- policy evaluation outputs

Large RL artifacts belong outside Git and likely outside the repository.

### 7.8 `runs/smoke/`

Purpose: optional local artifacts from smoke validations.

Owner: repository validation workflow.

Typical contents:

- command transcript
- captured logs
- readiness markers
- manifest

Smoke results intended for history should be summarized in docs, not committed as raw run folders.

### 7.9 `runs/validation/`

Purpose: local raw artifacts from validation workflows.

Owner: validation workflow.

Typical contents:

- clean clone command output
- build/launch log extracts
- validation manifest

Canonical validation reports belong in docs after sanitization.

### 7.10 `runs/tmp/`

Purpose: short-lived scratch execution directories.

Owner: local developer or automation task.

Policy:

- never commit
- safe to delete after review
- should not contain source-of-truth

## 8. Run Directory Naming Conventions

Recommended pattern:

```text
runs/<domain>/<yyyy-mm-dd>_<hhmmss>_<short_commit>_<scenario_slug>/
```

Example:

```text
runs/energyplus/2026-05-24_103012_2bd1c98_minimal_zone/
```

Rules:

- use local timestamp or UTC consistently; record timezone in manifest
- include a short git commit hash when available
- include a domain prefix through the parent folder
- use a short scenario slug when useful
- use lowercase
- use underscores or hyphens
- no spaces
- no private building names
- no personal names
- no client names
- avoid very long paths on Windows
- include a random or monotonic suffix if concurrent runs can collide

Reproducible naming may be useful for deterministic tests, but real runtime workflows should avoid
overwriting prior runs.

## 9. Run Manifest Policy

Each run should include a manifest:

```text
manifest.json
```

or:

```text
manifest.toml
```

Open decision: JSON is easier for tools; TOML is easier for humans. Pick one before backend
implementation.

Recommended manifest fields:

```text
run_id
created_at
timezone
domain
scenario
git_commit
git_status_summary
command
entrypoint
app_version
package_versions
backend_version
energyplus_version
input_files
input_hashes
config
output_paths
status
duration_seconds
errors
warnings
environment
privacy_classification
retention_policy
```

Manifests may contain local paths and environment data. They should not be committed without
sanitization.

## 10. Allowed Artifacts Inside Run Directories

Run directories may contain:

- input copies or references
- generated IDF files
- generated EnergyPlus outputs
- EPW reference metadata or approved copies
- logs
- stdout/stderr
- intermediate files
- result summaries
- metrics
- temporary checkpoints
- job status files
- command transcripts
- environment summaries
- manifests

Run directories may contain private or machine-specific information. Treat them as local-only by
default.

## 11. Git Policy for `runs/`

Policy:

- `runs/` should be ignored by default
- no run outputs committed by default
- raw run directories should not be staged
- `.gitkeep` only if an explicit ticket approves committing an empty folder
- small sanitized run summaries may be copied into docs/validation by explicit report ticket
- selected generated deliverables may be promoted to `outputs/`
- selected generated datasets may be promoted to `data/`
- promotion requires review, metadata, privacy check, and size check

Recommended future `.gitignore` policy:

```gitignore
/runs/
```

If the folder itself must exist in Git:

```gitignore
/runs/*
!/runs/.gitkeep
!/runs/README.md
```

Do not update `.gitignore` in this ticket.

## 12. Privacy and Retention Policy

Run directories may contain:

- private building data
- sensor data
- local absolute paths
- user names in paths
- environment variables
- solver logs
- generated models
- checkpoints
- proprietary inputs
- incomplete or erroneous outputs

Default policy:

- local-only
- ignored by Git
- not public
- deleted or archived by owner decision

Retention:

- short-lived scratch runs should be deleted after use
- important runs should be summarized in sanitized validation reports
- reproducible benchmark runs may be archived outside Git
- large runs should move to artifact storage if retained

Public report sanitization:

- remove local usernames and private paths
- remove private building identifiers
- remove sensor IDs unless synthetic
- include only relevant excerpts
- include commit hash and commands
- avoid raw full logs unless approved

## 13. EnergyPlus Run Policy

EnergyPlus run directories should be isolated and self-describing.

Recommended contents:

```text
runs/energyplus/<run_id>/
  manifest.json
  input/
    model.idf
    weather.epw          # optional copy only if allowed
  logs/
    stdout.log
    stderr.log
  output/
    eplusout.err
    eplusout.eso
    eplusout.csv
    eplusout.sql
  summary/
    parsed_results.json
```

Policy:

- executable path should be recorded in manifest only as needed and sanitized before public reports
- EnergyPlus version should be recorded
- IDF input may be copied for reproducibility or referenced with hash
- EPW/weather files may be copied only if license and size allow; otherwise reference with path/hash
- eplusout files are run artifacts and should not be committed by default
- errors and warnings should be summarized
- stdout/stderr should be captured
- no solver output should be written into source, backend, examples, or data directories by default

## 14. Calibration, Dataset, Surrogate, Control, and RL Run Policy

### Calibration

Calibration runs may include parameter sweeps, optimizer state, metric histories, and candidate model
inputs. They are local run artifacts until promoted.

### Dataset Generation

Dataset generation runs may create large candidate datasets. Generated datasets do not belong in Git
by default. Promotion to `data/` or artifact storage requires metadata, privacy review, and owner
approval.

### Surrogates

Surrogate training runs may create logs, metrics, checkpoints, and trained models. Temporary
checkpoints may live in `runs/`; long-term model artifacts need a future model/artifact policy.

### Control and RL

Control/RL runs may include action traces, reward logs, safety metrics, policies, replay buffers, and
checkpoints. These can be large and sensitive. They should not be committed by default.

### TensorBoard and ML Logs

TensorBoard or similar logs are allowed inside local run directories when generated by a run. They
should not be committed and should be promoted only through artifact storage if needed.

## 15. Runs and Outputs Boundary

Rules:

- `runs/` are raw execution directories
- `outputs/` are promoted generated deliverables or reports
- outputs may summarize selected run results
- not every run produces an output
- outputs must not be generated inside source or backend directories
- outputs must carry provenance back to the run id or manifest when possible

## 16. Runs and Data Boundary

Rules:

- runs may consume data
- runs may generate candidate datasets
- generated datasets do not become `data/` automatically
- promotion to `data/` requires approval, metadata, privacy review, and size review
- source input data should not be mutated in place by run workflows

## 17. Codex Access Policy for Runs

Codex may:

- inspect run directories if explicitly provided or requested
- generate run directories only when a task explicitly allows execution
- summarize generated artifacts after execution
- recommend cleanup or promotion steps

Codex must:

- not commit raw run directories
- not run long simulations without permission
- not run EnergyPlus unless explicitly requested
- respect output root restrictions
- avoid destructive cleanup unless explicitly authorized
- report generated paths after execution
- avoid writing run outputs into source directories

Codex must not:

- create `runs/` during architecture-only tickets
- silently delete run directories
- copy private run artifacts into docs
- promote run outputs to `data/` or `outputs/` without approval
- stage or commit run artifacts by default

## 18. Current Run-Like Artifact Classification

| Current artifact | Classification | Recommendation |
| --- | --- | --- |
| `_build/` | generated Kit build/runtime artifact, not `runs/` | Keep ignored. Do not commit. Do not manually edit. Regenerated by Kit workflow. |
| `_repo/` | Kit repo-tool cache/log state, not `runs/` | Keep ignored. Do not commit. Used by repo tooling. |
| `_compiler/` | Kit/compiler toolchain state, not `runs/` | Keep ignored. Do not commit. |
| `_repo/repo.log` | Kit tooling log | Keep ignored. Do not commit. |
| `_build/windows-x86_64/release/*` | generated app/test scripts and runtime state | Keep ignored. Not a product run directory. |
| Kit logs under user profile referenced by validation report | external local runtime logs | Do not commit raw logs. Use sanitized excerpts in validation reports. |
| `C:/temp/energy_model.idf` default placeholder | current local output behavior | Future run candidate. Replace with controlled `runs/energyplus` or output root policy when backend exists. |
| `C:/temp` and `C:/tmp` allowed roots | MVP output safety roots | Transitional. Future backend should use configured run roots. |
| future EnergyPlus `eplusout.*` files | run artifacts | Belong under `runs/energyplus/<run_id>/output`; do not commit by default. |
| future smoke validation raw logs | run/validation artifacts | Keep under `runs/smoke` or `runs/validation` locally; summarize in docs only after sanitization. |
| future dataset generation shards | run artifacts until promoted | Keep local or artifact-store. Do not commit automatically. |
| future model checkpoints | run/artifact-store candidates | Do not commit. Model artifact policy required. |

## 19. Open Decisions

Open decisions:

1. Whether to create `runs/` now or only when first backend execution exists.
2. Whether manifests should be JSON or TOML.
3. Retention duration for local runs.
4. Whether run directories should copy inputs or reference inputs with hashes.
5. How to handle large runs and artifact storage.
6. Whether smoke validation should write raw logs to `runs/smoke`.
7. How to sanitize validation reports derived from runs.
8. How to handle Windows path length limits and spaces.
9. How to handle concurrent run creation and collision-free IDs.
10. Whether future backend config should allow custom run roots outside the repository.
11. Whether generated outputs should live inside each run or be split immediately into `outputs/`.

## 20. Risks

- Run directories can contain private building/sensor data.
- Run directories can contain local usernames, paths, and environment details.
- Large simulation outputs can make the repo unusable if accidentally committed.
- EnergyPlus outputs can be numerous and confusing without manifests.
- Generated datasets can be mistaken for curated `data/`.
- Raw validation logs can expose private paths or machine details.
- Concurrent runs can overwrite one another without unique naming.
- Windows path length and spaces can break external tools.
- Cleanup can destroy useful evidence if retention is not decided first.

## 21. Recommended Future Tickets

Recommended follow-up tickets:

1. Define `outputs/` structure and promotion policy.
2. Decide whether to add `/runs/` to `.gitignore` before the first backend execution.
3. Define run manifest format and template.
4. Replace MVP `C:/temp/energy_model.idf` behavior with configured run/output root policy.
5. Design safe EnergyPlus backend run directory creation before enabling `run_energyplus`.
6. Define artifact storage policy for large runs, generated datasets, and model checkpoints.
