# Data Repository Structure Contract

Status: proposed architecture contract  
Scope: future root `data/` structure only  
Date: 2026-05-24  

## 1. Purpose

This document defines the intended future root-level `data/` structure for curated, approved,
small-to-moderate input datasets and data manifests.

This is a design contract only. It does not create `data/`, move files, add datasets, edit source,
run simulations, stage, commit, or push.

The repository is public. Data policy must assume that anything committed can become public, copied,
indexed, and difficult to remove later.

## 2. Current Data State Observed

There is currently no root-level `data/` directory.

Data-like files observed during inspection:

```text
DT.xlsx
~$DT.xlsx
.vscode/launch.json
.vscode/settings.json
.vscode/tasks.json
source/rendered_template_metadata.json
source/extensions/custom.aec.thermal_viz/data/sample_temperature_day.csv
source/extensions/my_company.my_usd_composer_setup_extension/layouts/default.json
templates/extensions/*/template/layouts/*.json
_build/windows-x86_64/*/compile_commands.json
_build/windows-x86_64/*/dev/repo.json
```

Tracked data-like files are mostly configuration, Kit layout source, template layout source, or
extension-local sample data. Generated `_build` JSON files are ignored build artifacts and are not
source-of-truth.

Observed project dataset candidate:

```text
source/extensions/custom.aec.thermal_viz/data/sample_temperature_day.csv
```

This is a small synthetic-looking extension-local telemetry sample with `timestamp,temp` columns and
15-minute intervals. It is currently correctly owned by the thermal visualization extension.

Observed root owner-decision data files:

```text
DT.xlsx
~$DT.xlsx
```

`DT.xlsx` is an untracked spreadsheet and requires owner review before any classification as public
data. `~$DT.xlsx` is an Office lock file and should not be committed.

## 3. Architectural Role of Future Root `data/`

Future root `data/` should contain curated input data that is:

- intentionally part of the repository
- approved for public visibility
- small-to-moderate in size
- documented with metadata and provenance
- reusable across examples, packages, backend workflows, or analysis
- not generated runtime output
- not private building/sensor/client data

Root `data/` is not a scratch area and not a default destination for generated datasets. Data enters
`data/` only after governance approval.

## 4. What Belongs in `data/`

Suitable future `data/` content:

- curated synthetic datasets
- approved small telemetry datasets
- approved public weather snippets or references
- approved EnergyPlus input datasets
- small USD/USDA model datasets if they are reusable data, not examples
- dataset manifests
- external data pointers
- schema/metadata documents for committed datasets
- small derived datasets promoted from outputs through approval

## 5. What Does Not Belong in `data/`

Do not place these in root `data/`:

- runtime run folders
- generated simulation outputs
- EnergyPlus ESO/SQL output dumps
- unreviewed generated datasets
- private building data
- real sensor data without anonymization and approval
- personal data
- client/project confidential data
- credentials or secrets
- local machine config
- Office lock files such as `~$*.xlsx`
- large weather libraries
- trained models or checkpoints by default
- notebooks as primary data storage
- vendor binaries
- EnergyPlus installation folders
- `_build`, `_repo`, or `_compiler` artifacts

## 6. Difference From Related Areas

### 6.1 `data/` vs `examples/`

Examples demonstrate usage. Data provides reusable curated inputs.

Tiny tutorial samples may live under `examples/` when they serve a single demonstration. Reusable
datasets that multiple workflows consume may belong in `data/` after governance approval.

### 6.2 `data/` vs `tests/fixtures/`

Test fixtures are tiny and assertion-oriented. They should be optimized for stable automated tests.

`data/` may contain larger curated inputs, but tests should not depend on large `data/` files by
default. If tests need data-derived inputs, use small approved slices under `tests/fixtures/`.

### 6.3 `data/` vs `runs/`

`runs/` should contain execution directories for simulations, calibration jobs, dataset generation,
and backend workflows.

`data/` should contain curated inputs. A generated run output does not become data automatically.

### 6.4 `data/` vs `outputs/`

`outputs/` should contain generated reports, exports, analysis outputs, and result artifacts.

`data/` should contain input/source datasets. Promotion from `outputs/` to `data/` requires owner
approval, metadata, provenance, and size/privacy review.

### 6.5 `data/` vs `references/`

`references/` should contain citations, external links, summarized reference material, or pointers to
standards.

`data/` should contain actual approved data files or data manifests. Large external datasets should
usually be referenced, not copied into Git.

### 6.6 `data/` vs extension-local `data/`

Extension-local `data/` contains assets required by an extension: icons, previews, setup assets,
template files, or extension-specific sample data.

Root `data/` is for repository-level curated datasets independent of one extension's runtime
packaging.

## 7. Proposed Future Root Layout

Recommended future layout:

```text
data/
  README.md
  curated/
  synthetic/
  telemetry/
  weather/
  energyplus/
  usd/
  manifests/
  external/
```

Create these folders only when approved data exists. This ticket does not create them.

## 8. Data Category Policy

### 8.1 `data/README.md`

Purpose: data index and governance entry point.

Should include:

- public/private policy
- dataset list
- size policy
- metadata requirements
- artifact storage policy
- contact/owner decision notes
- how to add or update data

### 8.2 `data/curated/`

Purpose: approved reusable datasets.

Ownership:

- project data governance
- owner approval required before commit

Allowed:

- small public-safe datasets
- synthetic datasets that are stable and documented
- derived datasets with reproducible generation notes

### 8.3 `data/synthetic/`

Purpose: synthetic datasets intentionally generated for the project.

Allowed:

- small synthetic telemetry sets
- synthetic building parameter tables
- synthetic simulation input sets

Generated datasets must not be dropped here automatically. Promotion requires metadata and approval.

### 8.4 `data/telemetry/`

Purpose: approved telemetry datasets.

Allowed:

- synthetic sensor time series
- anonymized real telemetry after approval
- schema-documented CSV/JSON samples

Requirements:

- timezone or local-time convention
- sampling rate
- units
- sensor ID anonymization
- building/zone anonymization

### 8.5 `data/weather/`

Purpose: approved weather data or weather manifests.

Allowed:

- small license-safe weather snippets
- manifests pointing to external weather sources
- documented EPW references

Most EPW/weather libraries should live outside Git or in an artifact store.

### 8.6 `data/energyplus/`

Purpose: curated EnergyPlus input data.

Allowed:

- approved small IDF inputs
- IDF fragments used by workflows
- manifests for EnergyPlus datasets

Not allowed:

- EnergyPlus install/vendor binaries
- bulk simulation outputs
- unreviewed EPW libraries
- ESO/SQL output dumps

### 8.7 `data/usd/`

Purpose: approved reusable USD data/model inputs.

Allowed:

- small synthetic USD/USDA building models
- reusable AEC convention data

Private building models should not be committed.

### 8.8 `data/manifests/`

Purpose: dataset metadata and external artifact manifests.

Allowed:

- dataset manifests
- file hashes
- source/provenance descriptions
- artifact store pointers
- generation references

### 8.9 `data/external/`

Purpose: lightweight pointers to external datasets, not bulk copies.

Allowed:

- README files
- download instructions
- license notes
- checksums
- external URLs when public and stable

Do not use this folder to vendor large third-party data into Git.

## 9. Data Size Policy

Default policy:

- small text files may be committed after approval
- medium files require owner approval
- large files should live outside Git
- binary files require stronger justification than text files
- generated bulk datasets should not be committed by default

Recommended thresholds:

| Size | Policy |
| --- | --- |
| Under 1 MB per file | Usually acceptable if public-safe, documented, and useful. |
| 1-10 MB per file | Owner approval required; consider whether Git is appropriate. |
| Over 10 MB per file | Prefer Git LFS or external artifact storage. |
| Over 50 MB per dataset | External artifact storage by default. |
| Any private or sensitive dataset | Do not commit to public repo. |

Git LFS may be appropriate for approved binary datasets, but it must be a deliberate repository policy,
not an ad hoc fix.

## 10. Privacy Policy

Data privacy rules:

- no private building data without explicit approval
- no real sensor data without anonymization and approval
- no personal data
- no client/project confidential data
- no credentials or secrets
- no private local paths in committed metadata
- no hidden identifiers in filenames, sensor IDs, zones, sheets, or metadata
- public-domain or synthetic data preferred

Anonymization requirements for real telemetry/building data:

- replace sensor IDs with neutral IDs
- replace room/zone names with neutral names
- remove addresses and coordinates unless intentionally public
- remove owner, tenant, client, or occupant identifiers
- document what was anonymized
- document residual risk

## 11. Provenance and Metadata Policy

Each committed dataset should include metadata. For a dataset folder, use a README or manifest.

Required metadata:

- dataset name
- owner/maintainer
- source/origin
- license
- date acquired or generated
- whether data is synthetic, measured, or derived
- generation script reference, if generated
- schema/columns
- units
- timezone or time convention
- sampling rate, if time-series
- file format
- size
- known limitations
- privacy/anonymization status
- intended use
- whether it is safe for public repo

Recommended manifest fields:

```text
name
version
source
license
created_at
generated_by
schema
units
timezone
sampling_rate
privacy
limitations
files
checksums
```

## 12. Data and Examples Boundary

Examples are for demonstration. Data is for reusable curated inputs.

Rules:

- tiny tutorial samples may stay under `examples/`
- reusable datasets belong in `data/` only after approval
- examples may reference datasets from `data/`
- examples must not mutate `data/`
- example outputs must go to `runs/` or `outputs/`

## 13. Data and Tests Boundary

Tests should be deterministic and fast by default.

Rules:

- `tests/fixtures` should hold tiny assertion-oriented inputs
- tests should not depend on large `data/` files by default
- small slices derived from `data/` may be copied into fixtures if stable and approved
- package tests should use minimal fixtures, not full datasets
- integration tests may reference `data/` only when explicitly marked

## 14. Data, Runs, and Outputs Boundary

Rules:

- `data/` is input/source data
- `runs/` are execution directories
- `outputs/` are generated results/reports
- generated datasets should not automatically go to `data/`
- promotion from `runs/` or `outputs/` to `data/` requires approval
- promoted data must include metadata, license, and provenance

## 15. EnergyPlus Data Policy

EnergyPlus-related rules:

- IDF examples are different from curated IDFs
- tiny illustrative IDF snippets may belong in `examples/energyplus`
- reusable approved IDF inputs may belong in `data/energyplus`
- EPW/weather files require license and size review
- large weather libraries should live outside Git or in artifact storage
- simulation outputs such as ESO, SQL, CSV, reports, and logs do not belong in `data/`
- EnergyPlus installation/vendor binaries do not belong in `data/`
- generated IDFs from runs are outputs unless explicitly promoted

Small canonical EnergyPlus fixtures may belong in `tests/fixtures` if they are assertion-oriented and
not general data.

## 16. Telemetry Data Policy

Telemetry rules:

- synthetic telemetry is preferred
- real telemetry requires anonymization and owner approval
- timestamps must define timezone or local-time convention
- units must be explicit
- sampling rate must be explicit
- sensor IDs must be anonymized or synthetic
- building/zone identifiers must be anonymized
- CSV/JSON schema must be documented
- missing data policy should be documented

Recommended CSV fields for simple telemetry:

```text
timestamp,temp_c
```

Recommended JSON concepts:

```text
timestamp
sensor_id
zone_id
channels
units
```

## 17. Model and Checkpoint Policy

Trained models and checkpoints do not belong in `data/` by default.

Policy:

- use future artifact storage or a dedicated `models/` policy
- commit only tiny illustrative model artifacts with explicit approval
- do not commit production checkpoints
- do not commit private training data through model artifacts
- document training data provenance for approved model artifacts

File types such as `.onnx`, `.pt`, `.pth`, `.pkl`, and `.h5` require explicit approval before commit.

## 18. Codex Data Access Policy

Codex may:

- inspect data-like files for classification
- create synthetic toy data only when explicitly requested
- update metadata when adding approved data
- recommend data policies and manifests

Codex must:

- not commit private or real data without approval
- not add large files without approval
- not modify curated data silently
- not generate outputs into `data/`
- not treat Office lock files as data
- not promote root owner-decision files into data without review
- document provenance for any approved data it creates

Codex must not:

- create `data/` during architecture-only tickets
- run simulations to generate data unless explicitly requested
- add vendor data or weather libraries without license review
- add secrets or local configs
- modify `.gitignore` for data policy unless the ticket explicitly allows it

## 19. Current Data-Like File Classification

| Current path | Classification | Recommendation |
| --- | --- | --- |
| `source/extensions/custom.aec.thermal_viz/data/sample_temperature_day.csv` | extension-local telemetry sample | Stay extension-local for now. Future `data/telemetry` or `examples/telemetry` candidate only if promoted with metadata. |
| `DT.xlsx` | unknown root spreadsheet / owner-decision data-like file | Owner review required. Do not commit or move until contents, privacy, and purpose are classified. |
| `~$DT.xlsx` | temporary Office lock file | Should not commit. Future ignore/cleanup candidate. |
| `.vscode/launch.json` | shared dev configuration, not dataset | Keep governed by dev config policy, not `data/`. |
| `.vscode/tasks.json` | shared dev configuration, not dataset | Keep governed by dev config policy, not `data/`. |
| `.vscode/settings.json` | local/shared config depending status | Not data. Review separately under local developer configuration policy. |
| `source/rendered_template_metadata.json` | generated/template metadata | Not data. Owner decision/generation policy item. |
| `source/extensions/my_company.my_usd_composer_setup_extension/layouts/default.json` | extension layout asset | Stay extension-local. Not dataset. |
| `templates/extensions/*/template/layouts/*.json` | Kit template scaffolding | Stay under `templates/`. Not data. |
| `_build/windows-x86_64/*/*.json` | generated build artifacts | Do not commit; ignored generated state. |
| setup extension material assets under `data/` | extension runtime/template assets | Stay extension-local; not root data. |
| sketch extension icons/previews under `data/` | extension metadata assets | Stay extension-local; not root data. |
| future `.idf` files | depends on purpose | Examples, fixtures, `data/energyplus`, or outputs depending on approval and provenance. |
| future `.epw` files | weather data | License/size review required; likely external/artifact store unless tiny and approved. |
| future `.eso`, `.sql`, simulation CSV outputs | generated outputs | Belong under `runs/` or `outputs/`, not `data/` by default. |
| future `.onnx`, `.pt`, `.pth`, `.pkl`, `.h5` | model/checkpoint artifacts | Do not commit by default; artifact/model policy required. |

## 20. Open Decisions

Open decisions:

1. Whether to create `data/` before actual approved datasets exist.
2. Whether to use Git LFS.
3. Which artifact storage system should hold large datasets and model artifacts.
4. Whether the project needs separate public/private data locations.
5. Weather file policy for EPW inputs.
6. Telemetry anonymization standard.
7. Dataset versioning strategy.
8. Generated dataset promotion process from `runs/` or `outputs/`.
9. Whether `DT.xlsx` contains project data, planning notes, or private information.
10. Maximum committed dataset size for this public repository.
11. Whether future data manifests should be JSON, YAML, TOML, or Markdown.

## 21. Risks

- Public repository exposure can leak private building, sensor, client, or thesis data.
- Root `data/` can become a dumping ground if approval and metadata are not enforced.
- Large files can make Git slow and expensive to clone.
- Weather and vendor datasets can have license restrictions.
- Generated outputs can be mistaken for curated source data.
- Tests can become slow or brittle if they depend on large datasets.
- Model artifacts can leak training data or lock the repo into binary storage problems.
- Office lock files can be accidentally staged if ignored/cleanup policy is incomplete.

## 22. Recommended Future Tickets

Recommended follow-up tickets:

1. Classify `DT.xlsx` with owner review: public data, private data, planning artifact, or ignore.
2. Add ignore policy for Office lock files if not already covered.
3. Define `runs/` and `outputs/` structure before generating simulation outputs.
4. Decide Git LFS and artifact storage policy.
5. Create a dataset manifest template before adding root `data/`.
6. Define telemetry anonymization and schema conventions.
