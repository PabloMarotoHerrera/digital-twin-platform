# Outputs Repository Structure Contract

Status: proposed architecture contract  
Scope: future root `outputs/` structure only  
Date: 2026-05-24  

## 1. Purpose

This document defines the intended future root-level `outputs/` structure for promoted generated
deliverables, reports, exports, summaries, processed results, visualizations, and publication-ready
artifacts.

This is a design contract only. It does not create `outputs/`, generate outputs, run EnergyPlus, run
simulations, edit source, update `.gitignore`, stage, commit, or push.

The repository is public. Generated outputs must be reviewed before commit because they may include
private model data, local paths, logs, environment details, large binary files, or generated artifacts
that are not source-of-truth.

## 2. Current Output-Like State Observed

There is currently no root-level `outputs/` directory and no root-level `runs/` directory.

Output-like files observed during inspection are primarily:

- Kit/readme images under `readme-assets/`
- extension metadata images under `source/extensions/*/data/`
- template metadata/images/layout files under `templates/`
- generated Kit JSON/log files under `_build/`
- Kit repo tooling log under `_repo/repo.log`
- current MVP IDF export defaults pointing at `C:/temp/energy_model.idf`
- architecture/validation documents under `docs/architecture/`

These are not root `outputs/` today. They are either source assets, template assets, generated Kit
artifacts, local logs, or documentation reports.

## 3. Architectural Role of Future Root `outputs/`

Future root `outputs/` should contain selected generated artifacts that have been promoted from raw
execution state into deliberate deliverables.

Suitable `outputs/` content:

- generated reports
- exported models/files
- processed summaries
- visualizations/screenshots
- processed EnergyPlus results
- calibration summaries
- generated dataset deliverables after review
- public-safe model evaluation artifacts
- validation outputs after sanitization
- public-safe deliverables

Raw execution state belongs in `runs/`. Curated input data belongs in `data/`. Narrative validation
reports belong in docs.

## 4. What Does Not Belong in `outputs/`

Do not place these in `outputs/`:

- source code
- raw run directories
- unreviewed generated artifacts
- private building/sensor data
- raw logs with local paths or secrets
- curated source datasets
- tutorial examples
- test snapshots by default
- generated build outputs from `_build`
- Kit repo/tooling caches
- vendor binaries
- EnergyPlus installation folders
- large datasets without artifact policy
- trained models/checkpoints by default
- secrets or credentials
- temporary debugging dumps

## 5. Difference From Related Areas

### 5.1 `outputs/` vs `runs/`

`runs/` contains raw execution directories. `outputs/` contains selected, promoted, cleaned, or
summarized deliverables derived from runs.

Not every run produces an output. Raw `eplusout.*`, full logs, intermediate files, and scratch
checkpoints stay in `runs/` unless explicitly promoted.

### 5.2 `outputs/` vs `data/`

`data/` contains curated input/source datasets. `outputs/` contains generated result artifacts.

A generated dataset may begin in `runs/`, be reviewed as an output, and only later be promoted to
`data/` if it becomes a curated reusable input dataset.

### 5.3 `outputs/` vs `docs/validation/`

Docs contain narrative validation reports and architecture contracts. `outputs/` contains generated
artifacts.

Validation reports may live in docs. Raw validation logs should remain local in `runs/` or be promoted
to `outputs/validation` only after sanitization.

### 5.4 `outputs/` vs `examples/`

Examples demonstrate workflows and provide small runnable/loadable inputs. Outputs are generated
deliverables.

Examples may produce outputs, but generated files should go to `runs/` or `outputs/`, not into
`examples/`.

### 5.5 `outputs/` vs `tests/snapshots/`

Test snapshots are assertion baselines. Outputs are deliverables.

Do not reuse arbitrary generated outputs as snapshots without explicit approval. Snapshots must be
small, stable, and owned by tests.

### 5.6 `outputs/` vs `_build`, `_repo`, and `_compiler`

`_build`, `_repo`, and `_compiler` are Kit-managed generated/tooling areas. They are not product
deliverable output roots.

Do not copy or edit Kit-managed generated state into `outputs/` unless an explicit report/export task
sanitizes and promotes a specific artifact.

## 6. Proposed Future Root Layout

Recommended future layout:

```text
outputs/
  README.md
  reports/
  exports/
  summaries/
  visualizations/
  simulation/
  energyplus/
  calibration/
  datasets/
  models/
  validation/
  public/
  tmp/
```

This ticket does not create these folders. If `outputs/` is created later, it should be ignored by
default unless a specific public-safe promotion policy is approved.

## 7. Output Category Policy

### 7.1 `outputs/reports/`

Purpose: generated reports that are not hand-authored docs.

Examples:

- generated PDF/HTML analysis reports
- generated simulation summaries
- generated benchmark reports

Ownership: producing workflow plus documentation owner for public publication.

### 7.2 `outputs/exports/`

Purpose: exported files from app/backend/package workflows.

Examples:

- exported IDF files selected for review
- exported USD/USDA files
- exported CSV summaries
- exported JSON result bundles

Raw exports from a single run should start under `runs/`; `outputs/exports` is for selected artifacts.

### 7.3 `outputs/summaries/`

Purpose: compact processed summaries derived from runs.

Examples:

- KPI summaries
- error/warning summaries
- normalized result tables
- compact JSON metrics

### 7.4 `outputs/visualizations/`

Purpose: generated visual artifacts.

Examples:

- screenshots
- rendered images
- plots
- charts
- HTML visual reports
- video/GIF exports when approved

Visual outputs must be reviewed for privacy, size, and environment dependence.

### 7.5 `outputs/simulation/`

Purpose: processed generic simulation outputs independent of a specific solver.

Examples:

- normalized simulation summaries
- scenario comparison tables
- run comparison reports

### 7.6 `outputs/energyplus/`

Purpose: processed EnergyPlus outputs promoted from raw run folders.

Examples:

- parsed summaries
- selected CSV result tables
- error/warning summaries
- public-safe HTML reports
- selected exported IDFs when intentionally promoted

Raw `eplusout.*` stays in `runs/energyplus`.

### 7.7 `outputs/calibration/`

Purpose: calibration deliverables.

Examples:

- calibrated parameter summaries
- optimization traces after reduction
- comparison charts
- final metrics tables

### 7.8 `outputs/datasets/`

Purpose: generated dataset deliverables before or instead of promotion to `data/`.

Examples:

- generated dataset manifests
- dataset quality reports
- small public-safe dataset slices

Large generated datasets require artifact storage and should not be committed.

### 7.9 `outputs/models/`

Purpose: model-related deliverables after explicit approval.

Examples:

- model cards
- evaluation reports
- tiny illustrative model artifacts if approved

Trained checkpoints and production model binaries should not be committed by default.

### 7.10 `outputs/validation/`

Purpose: generated validation artifacts after sanitization.

Examples:

- sanitized command output bundles
- validation summaries
- small public-safe log excerpts

Narrative validation reports belong in docs.

### 7.11 `outputs/public/`

Purpose: explicitly public-safe deliverables.

Policy:

- every artifact must be reviewed
- no private paths
- no private data
- no secrets
- metadata must state public-safe status

### 7.12 `outputs/tmp/`

Purpose: short-lived generated outputs not intended for commit.

Policy:

- ignored
- safe to delete after review
- not source-of-truth

## 8. Promotion Policy

Outputs should be promoted from `runs/`, not generated directly into source directories.

Promotion requires:

- source run id
- source git commit
- metadata
- privacy review
- size review
- intended-use statement
- owner approval for public commit
- file hashes for nontrivial artifacts

Promotion process:

1. Generate raw artifacts under `runs/`.
2. Select specific useful artifacts.
3. Sanitize paths, logs, private labels, and secrets.
4. Convert or reduce large raw outputs into compact deliverables when possible.
5. Write metadata.
6. Decide whether artifact stays local, moves to external storage, or is committed.
7. Commit only if explicitly approved and public-safe.

## 9. Output Metadata Policy

Each promoted output should include metadata:

```text
metadata.json
```

or:

```text
metadata.toml
```

Open decision: JSON is easier for automation; TOML is easier for manual editing.

Recommended metadata fields:

```text
output_id
created_at
source_run_id
git_commit
source_inputs
generation_command
generated_by
tool_versions
file_list
file_hashes
privacy_classification
license
provenance
intended_use
retention_policy
public_safe
limitations
```

Metadata itself must also be reviewed for private paths or sensitive environment details.

## 10. Git Policy for Outputs

Policy:

- `outputs/` should be ignored by default
- raw generated outputs should not be committed
- large outputs should not be committed
- private outputs should not be committed
- tiny canonical outputs may be committed only with explicit approval
- public-safe outputs require metadata
- output folders may include a committed `README.md` or `.gitkeep` only if approved

Recommended future `.gitignore` policy:

```gitignore
/outputs/
```

If the folder itself must exist in Git:

```gitignore
/outputs/*
!/outputs/README.md
!/outputs/.gitkeep
```

Do not edit `.gitignore` in this ticket.

## 11. Size and Artifact Storage Policy

Recommended thresholds:

| Artifact type | Policy |
| --- | --- |
| Small text output under 1 MB | Commit only if public-safe, canonical, and approved. |
| Medium text/binary output 1-10 MB | Owner approval required; consider Git LFS or artifact storage. |
| Large output over 10 MB | External artifact storage by default. |
| Generated dataset | Artifact storage or `data/` promotion process; not direct commit. |
| Model checkpoint | Artifact/model storage by default. |
| Video/GIF export | Artifact storage by default unless tiny and approved. |
| Raw logs | Do not commit by default; sanitize excerpts instead. |

Git LFS may be useful for approved binary deliverables, but must be adopted deliberately.

## 12. Privacy and Publication Policy

Outputs must be reviewed before publication.

Forbidden in public outputs:

- private building data
- real sensor data without anonymization
- local usernames
- local absolute paths
- raw logs with environment secrets
- client/project confidential data
- API keys, tokens, credentials
- private prompts
- private screenshots

Sanitization requirements:

- remove private paths
- anonymize building/zone/sensor identifiers
- remove secrets and environment variables
- reduce raw logs to relevant excerpts
- state public-safe status in metadata

## 13. EnergyPlus Output Policy

EnergyPlus output policy:

- raw `eplusout.*` belongs in `runs/energyplus/<run_id>/output`
- processed summaries may be promoted to `outputs/energyplus`
- CSV/SQL/HTML reports require size and privacy review
- errors/warnings may be summarized into compact reports
- generated IDF files are usually run artifacts unless promoted as exports or examples
- output provenance should link to run manifest
- EnergyPlus executable paths should not be published without review
- weather file paths should be sanitized

Possible promoted outputs:

- `summary.json`
- `warnings.md`
- `zone_temperature_summary.csv`
- `energyplus_report.html` after review

## 14. Visualization Output Policy

Visualization outputs include:

- screenshots
- rendered images
- viewport captures
- plots
- charts
- HTML reports
- videos/GIFs

Policy:

- visual outputs require public/private review
- screenshots must not expose private project data
- environment-dependent visuals should record OS/GPU/driver/Kit version if used for validation
- deterministic plots are preferred over raw viewport screenshots when possible
- docs may embed selected public-safe visual outputs or maintain separate docs images
- video/GIF exports should usually use artifact storage

## 15. Generated Dataset and Model Artifact Policy

Generated datasets:

- start in `runs/`
- may be summarized under `outputs/datasets`
- may be promoted to `data/` only after governance approval
- large datasets require artifact storage
- metadata must record generation command, source inputs, schema, privacy status, and provenance

Model artifacts:

- checkpoints and trained models should not be committed by default
- model evaluation reports may be promoted to `outputs/models`
- model cards may be committed if public-safe
- model binaries require future artifact/model policy
- metadata must record training data provenance and limitations

## 16. Outputs and Docs Boundary

Docs contain narrative reports, architecture contracts, and validation reports.

Outputs contain generated artifacts.

Rules:

- validation reports may live in docs
- raw validation logs remain local or go to `outputs/validation` only after sanitization
- docs may link to public-safe outputs
- do not use `outputs/` for hand-authored architecture docs
- do not use docs as bulk artifact storage

## 17. Outputs and Test Snapshots Boundary

Rules:

- test snapshots are assertion baselines
- outputs are deliverables
- do not reuse arbitrary outputs as snapshots without approval
- snapshots must be stable, small, and test-owned
- output updates should not silently update test baselines

## 18. Codex Access Policy for Outputs

Codex may:

- generate outputs only when explicitly requested
- inspect output directories when explicitly requested
- summarize generated paths after execution
- create metadata for approved outputs
- recommend promotion or artifact storage

Codex must:

- not commit outputs by default
- not add large or private outputs
- sanitize outputs before docs/public promotion
- report generated paths
- avoid writing outputs into source directories
- respect configured output roots

Codex must not:

- create `outputs/` during architecture-only tickets
- delete outputs unless cleanup is explicitly authorized
- promote raw run artifacts without approval
- copy private logs into docs
- add model checkpoints or generated datasets to Git by default

## 19. Current Output-Like Artifact Classification

| Current artifact | Classification | Recommendation |
| --- | --- | --- |
| `_build/` | generated Kit tooling/runtime state, not `outputs/` | Keep ignored. Do not commit. |
| `_build/windows-x86_64/release/logs/**` | generated Kit logs | Keep ignored. Do not commit raw logs. Sanitized excerpts may appear in validation reports. |
| `_build/windows-x86_64/*/compile_commands.json` | generated build metadata | Keep ignored. Not a product output. |
| `_repo/` | Kit repo-tool cache/log state | Keep ignored. Not product output. |
| `_repo/repo.log` | Kit tooling log | Keep ignored. |
| `_compiler/` | compiler/toolchain state | Keep ignored. |
| `docs/architecture/clean_clone_validation_report.md` | documentation validation report | Belongs in docs, not `outputs/`. |
| other architecture contracts in `docs/architecture/` | hand-authored docs/contracts | Belong in docs, not `outputs/`. |
| `C:/temp/energy_model.idf` placeholder behavior | current local export behavior | Future run/export candidate; replace with controlled run/output root policy. |
| future `eplusout.*` | raw EnergyPlus run artifacts | Belong in `runs/energyplus`; processed summaries may be promoted. |
| future exported IDFs | run artifact or promoted export | Usually `runs`; may promote to `outputs/exports` or examples with metadata. |
| future generated plots/screenshots | visualization outputs | `outputs/visualizations` candidate after public/privacy review. |
| future generated datasets | run artifacts or data candidates | Usually artifact storage or data promotion process; not direct commit. |
| future model checkpoints | model artifacts | Artifact/model storage by default; do not commit. |
| readme images under `readme-assets/` | source documentation assets | Stay where they are; not `outputs/`. |
| extension icons/previews | extension metadata assets | Stay extension-local; not `outputs/`. |
| template icons/layouts | template/scaffolding assets | Stay under `templates/`; not `outputs/`. |

## 20. Open Decisions

Open decisions:

1. Whether to create `outputs/` now or only after first promoted artifact exists.
2. Whether `/outputs/` should be globally ignored.
3. Whether to allow committed public-safe outputs.
4. Metadata format: JSON or TOML.
5. Artifact storage choice.
6. Git LFS policy.
7. Model artifact policy.
8. Generated dataset promotion policy.
9. Visualization artifact policy and screenshot location.
10. Public/private split strategy.
11. Whether outputs should include `README.md` only, while artifacts live elsewhere.

## 21. Risks

- Outputs can accidentally expose private building/sensor data.
- Raw logs can expose usernames, local paths, environment variables, or secrets.
- Large generated files can make Git slow or unusable.
- Outputs can be mistaken for source-of-truth if metadata is missing.
- EnergyPlus outputs can be numerous and hard to interpret without provenance.
- Screenshots and visualizations can drift with UI, GPU, driver, and Kit changes.
- Model checkpoints and generated datasets can require artifact storage, not Git.
- Public-safe promotion can be skipped under delivery pressure.

## 22. Recommended Future Tickets

Recommended follow-up tickets:

1. Decide `.gitignore` policy for `/runs/` and `/outputs/` before first backend execution.
2. Define output metadata format and template.
3. Define artifact storage and Git LFS policy.
4. Replace MVP `C:/temp/energy_model.idf` export behavior with configured run/output root policy.
5. Define public-safe visualization/report publication workflow.
6. Define model artifact policy before surrogate/RL training outputs exist.
