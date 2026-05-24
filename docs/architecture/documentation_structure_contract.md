# Documentation Structure Contract

Status: proposed architecture contract  
Scope: repository documentation structure only  
Date: 2026-05-24  

## 1. Purpose

This document defines the intended `docs/` structure for the digital twin platform repository.
It is a documentation organization contract, not a migration ticket.

The repository is currently a public NVIDIA Omniverse Kit App Template derivative with a validated
clean-clone baseline. The product source-of-truth currently lives under `source/apps` and
`source/extensions`. Documentation must support that source structure without changing build,
launch, or Kit template behavior.

No files are moved, renamed, staged, committed, or deleted by this contract.

## 2. Current Documentation State

### 2.1 Current `docs/` tree in this working copy

The current local `docs/` tree contains:

```text
docs/
  07_USD_MODELING_CONVENTIONS.md
  architecture/
    current_repository_analysis_codex.md
    first_commit_source_classification.md
    generated_runtime_artifacts_policy.md
    source_repository_structure.md
```

Notes:

- `docs/07_USD_MODELING_CONVENTIONS.md` is currently a tracked domain convention document.
- `docs/architecture/current_repository_analysis_codex.md` is a broad architecture analysis report.
- `docs/architecture/generated_runtime_artifacts_policy.md` is a repository hygiene and generated-artifact policy.
- `docs/architecture/first_commit_source_classification.md` is a first-commit classification report and staging plan.
- `docs/architecture/source_repository_structure.md` is the current `source/` structure contract.
- The clean-clone validation report from Ticket 006/007 is part of the project history by task context, but this original working copy may not yet have pulled the pushed commit containing `docs/architecture/clean_clone_validation_report.md`.

### 2.2 Root documentation candidates

The repository root currently contains owner-decision documentation candidates:

```text
00_PROJECT_CONTEXT.txt
01_RULES_AND_LIMITATIONS.txt
02_TASKS_BACKLOG.txt
03_USD_CONVENTIONS.txt
04_CODEX_WORKFLOW.txt
05_MIGRATION_MAP.txt
06_EXTENSION_PLAYBOOK.txt
07_PROFESIONAL_VISUALIZATION.txt
current_repository_analysis.md
digital_twin_contexto_maestro.md
```

These files are not yet organized into `docs/` and should be treated as owner-decision items.
They may contain strategic planning, thesis context, project-specific workflow rules, or outdated
analysis. They should not be moved or committed into a public documentation structure without
owner review.

## 3. Intended Top-Level `docs/` Structure

The intended long-term documentation structure is:

```text
docs/
  README.md
  architecture/
  design/
  adr/
  development/
  roadmap/
  validation/
  research/
  thesis/
  diagrams/
  examples/
  references/
  archive/
```

Folders should be created only when a document actually belongs there. This contract does not require
empty folders.

## 4. Folder Ownership and Purpose

### 4.1 `docs/README.md`

The future documentation index. It should be the entry point for humans and Codex.

It should link to:

- active architecture contracts
- ADR index
- development workflow docs
- current roadmap
- latest validation status
- public research or thesis notes if approved
- archived or superseded material only when useful

### 4.2 `docs/architecture/`

Canonical architecture contracts and architecture analysis that governs repository structure,
ownership boundaries, source-of-truth policy, dependency direction, build/runtime separation, and
extension organization.

This folder should contain active architecture decisions that affect repository shape. It may also
temporarily contain analysis reports until a later docs reorganization separates reports from
contracts.

Examples:

- repository structure contracts
- `source/` structure contract
- generated/runtime artifact policy
- source-of-truth policy
- dependency direction policy
- Kit template integration policy

### 4.3 `docs/design/`

Product and domain design documents that describe how the platform should behave or model concepts.

Examples:

- USD modeling conventions
- AEC semantic modeling conventions
- viewport interaction design
- visualization behavior
- user workflow definitions
- extension feature designs

### 4.4 `docs/adr/`

Architecture Decision Records for durable decisions with alternatives and consequences.

ADRs should be used when a decision is narrow, explicit, and worth preserving as history, for example:

- keep Kit app source under `source/apps`
- keep local extensions under `source/extensions`
- choose a Python namespace policy
- decide whether EnergyPlus remains vendored or becomes an external dependency
- extract reusable domain logic into `packages/`

### 4.5 `docs/development/`

Developer workflow documentation.

Examples:

- local setup
- build and launch commands
- Codex workflow rules
- testing workflow
- extension authoring playbook
- release checklist
- troubleshooting

### 4.6 `docs/roadmap/`

Planning documents that describe intended future work. Roadmap documents are not architecture
contracts unless explicitly promoted.

Examples:

- migration maps
- backlog summaries
- phased cleanup plans
- feature sequencing
- milestone definitions

### 4.7 `docs/validation/`

Validation reports and reproducibility evidence.

Examples:

- clean-clone validation report
- build smoke test report
- launch smoke test report
- extension loading validation
- regression validation notes

Validation reports are evidence snapshots. They should include date, commit hash, environment,
commands run, result, and limitations.

### 4.8 `docs/research/`

Research notes that inform implementation but are not yet product contracts.

Examples:

- EnergyPlus integration research
- Omniverse/Kit API investigation notes
- agent orchestration experiments
- simulation workflow comparisons
- external references summarized for project use

Research notes require public/private review before being committed to a public repository.

### 4.9 `docs/thesis/`

Academic thesis material, methodology notes, dissertation outlines, or thesis-specific context.

This folder should be used only after owner approval because thesis material may include unpublished
ideas, institution-specific requirements, personal planning, or content that should not be public.

### 4.10 `docs/diagrams/`

Source diagrams and exported diagram assets.

Recommended future layout:

```text
docs/diagrams/
  source/
  exported/
```

Diagram source should be preferred over image-only diagrams. Mermaid or PlantUML embedded in Markdown
is preferred when possible. Draw.io, Excalidraw, SVG, PNG, or PDF exports are acceptable when the
source file is also preserved.

### 4.11 `docs/examples/`

Small documentation examples that support docs, not runtime examples required by extensions.

Examples:

- example commands
- example `.kit` snippets
- sample extension manifests for explanation
- sample USD conventions for documentation

Runtime sample assets required by extensions should remain with the owning extension unless they are
purely explanatory.

### 4.12 `docs/references/`

Reference material that is allowed to be committed and is useful for long-term project work.

Examples:

- summarized external references
- public links and citation lists
- standards references
- NVIDIA/Omniverse documentation link maps

Do not commit copyrighted, licensed, private, or large external documents here without explicit owner
approval.

### 4.13 `docs/archive/`

Superseded, deprecated, or historical documents retained for traceability.

Archived documents must be clearly marked as non-canonical and should link to their replacement when
one exists.

## 5. Future Placement of Current Documents

This section is a target organization map only. It does not authorize moves.

| Current path | Current role | Future recommended location | Recommendation |
| --- | --- | --- | --- |
| `docs/architecture/current_repository_analysis_codex.md` | analysis report | `docs/architecture/` or later `docs/archive/architecture/` | Keep as historical analysis; mark superseded when contracts replace it. |
| `docs/architecture/generated_runtime_artifacts_policy.md` | repository hygiene contract | `docs/architecture/` | Keep canonical until replaced by ADRs or a dedicated hygiene contract. |
| `docs/architecture/first_commit_source_classification.md` | first-commit planning report | `docs/validation/` or `docs/archive/first_commit/` | Preserve as historical staging evidence; not a live architecture contract. |
| `docs/architecture/clean_clone_validation_report.md` | validation report | `docs/validation/` | Keep as reproducibility evidence after syncing this working copy. |
| `docs/architecture/source_repository_structure.md` | architecture contract | `docs/architecture/` | Keep canonical for `source/` governance. |
| `docs/07_USD_MODELING_CONVENTIONS.md` | domain/design convention | `docs/design/usd_modeling_conventions.md` | Rename/move later; keep tracked in place until a migration ticket. |
| `00_PROJECT_CONTEXT.txt` | project context | `docs/development/project_context.md` or `docs/archive/` | Owner decision; convert to Markdown if kept. |
| `01_RULES_AND_LIMITATIONS.txt` | rules/constraints | `docs/development/rules_and_limitations.md` | Owner decision; review for public sensitivity. |
| `02_TASKS_BACKLOG.txt` | backlog | `docs/roadmap/backlog.md` | Owner decision; likely public only after sanitization. |
| `03_USD_CONVENTIONS.txt` | USD notes | merge into `docs/design/usd_modeling_conventions.md` | Owner decision; avoid duplicate canonical USD docs. |
| `04_CODEX_WORKFLOW.txt` | agent workflow | `docs/development/codex_workflow.md` | Owner decision; useful if public-safe. |
| `05_MIGRATION_MAP.txt` | migration planning | `docs/roadmap/migration_map.md` | Owner decision; mark as plan, not contract. |
| `06_EXTENSION_PLAYBOOK.txt` | extension workflow | `docs/development/extension_playbook.md` | Owner decision; useful after review. |
| `07_PROFESIONAL_VISUALIZATION.txt` | visualization guidance | `docs/design/professional_visualization.md` | Owner decision; fix naming typo during future migration if approved. |
| `digital_twin_contexto_maestro.md` | strategic/master context | `docs/research/`, `docs/thesis/`, private notes, or not committed | Owner review required before public commit. |
| `current_repository_analysis.md` | initial analysis | `docs/archive/` or exclude | Treat as superseded/non-canonical unless owner approves archival. |

## 6. Document Lifecycle Categories

### 6.1 Architecture contract

A normative document that governs future work. It should be updated deliberately and referenced by
tickets that depend on it.

Examples: repository structure contracts, dependency direction rules, generated artifact policy.

### 6.2 Design proposal

A proposed product, domain, or implementation design that is not yet accepted as architecture.
Design proposals may become ADRs, architecture contracts, or implementation tickets.

### 6.3 Analysis report

A point-in-time investigation. It may contain findings, risks, and recommendations, but it is not
automatically canonical.

### 6.4 Validation report

Evidence that a build, launch, clone, migration, or workflow succeeded or failed under specific
conditions. It should include command outputs or summaries, commit hash, environment, date, and known
limitations.

### 6.5 ADR

A concise durable decision record with status, context, decision, alternatives, and consequences.
ADRs are preferred for important binary or irreversible decisions.

### 6.6 Roadmap

Forward-looking planning. Roadmaps are expected to change and should not be treated as source-of-truth
for architecture unless they reference a contract or ADR.

### 6.7 Research note

Exploratory notes, external findings, experiments, or comparisons. Research notes require review
before promotion into design or architecture.

### 6.8 Thesis note

Academic or thesis-specific writing. These notes may be public, private, or partially public depending
on owner review.

### 6.9 Temporary working note

Short-lived notes used to support a task. Temporary notes should either be deleted before commit,
converted into a proper document, or archived with a clear reason.

### 6.10 Deprecated/archive

Historical material that is intentionally retained but no longer governs current work. Archived docs
must identify the active replacement when one exists.

## 7. Naming Conventions

Long-term documentation filenames should use lowercase snake_case:

```text
source_repository_structure.md
generated_runtime_artifacts_policy.md
usd_modeling_conventions.md
clean_clone_validation_report.md
```

ADRs should use a stable number and a short lowercase title:

```text
docs/adr/0001-keep-kit-source-under-source.md
docs/adr/0002-standardize-extension-namespace.md
```

Date prefixes may be used for reports when multiple snapshots are expected:

```text
docs/validation/2026-05-24-clean-clone-validation.md
docs/research/2026-05-24-energyplus-integration-notes.md
```

Rules:

- Prefer `.md` over `.txt` for repository documentation.
- Avoid ambiguous root-level documentation files long term.
- Avoid duplicate canonical documents for the same topic.
- Use English filenames unless there is an explicit owner decision to keep Spanish names for a category.
- Fix spelling during future migrations when renaming is already in scope.
- Do not encode ticket numbers in permanent filenames unless the document is explicitly historical.

## 8. Source-of-Truth Rules

The documentation source-of-truth hierarchy should be:

1. ADRs for explicit accepted decisions.
2. Architecture contracts for active repository and system structure.
3. Development docs for current workflow.
4. Validation reports for evidence tied to a commit and environment.
5. Design docs for domain/product behavior.
6. Roadmap and research notes for non-binding future direction.
7. Archived documents for historical traceability only.

Canonical documents must state their status. Recommended statuses:

- `draft`
- `proposed`
- `accepted`
- `superseded`
- `deprecated`
- `archived`

When a document is superseded:

- add a clear status line near the top
- link to the replacement document
- do not leave two active source-of-truth documents for the same rule
- avoid rewriting history unless the document is explicitly a living contract

Codex-generated documents should include enough context to be auditable:

- scope
- date
- whether it is analysis, policy, contract, or validation
- whether it was derived from actual repository inspection
- limitations or open decisions

## 9. Docs Index Policy

A future `docs/README.md` should be created as the documentation index.

Minimum recommended sections:

- Repository architecture
- Source tree contracts
- Development workflow
- Validation status
- ADR index
- Roadmap
- Domain/design conventions
- Research and thesis material, only if approved for public visibility
- Archived or superseded documents

The index should link to active documents only by default. Historical documents should be placed in a
separate archive section to avoid confusing them with current guidance.

## 10. Diagram Policy

Preferred diagram formats:

- Mermaid embedded in Markdown for simple architecture, sequence, dependency, and flow diagrams.
- PlantUML for more formal diagrams if the project standardizes on it.
- Draw.io or Excalidraw only when a visual editing workflow is needed.
- SVG or PNG for exports, not as the only source when the diagram is likely to change.

Rules:

- Store editable diagram sources under `docs/diagrams/source/`.
- Store exported images under `docs/diagrams/exported/`.
- Keep exports generated from source and name them consistently.
- Do not commit large binary diagrams without clear value.
- Do not use diagrams as a substitute for explicit dependency or ownership rules.

## 11. Codex Documentation Access Policy

Codex may edit:

- architecture contracts when a ticket explicitly requests architecture documentation
- development docs when documenting workflows or validation steps
- validation reports when a ticket requests evidence capture
- design docs when the ticket requests product/domain design documentation

Codex may inspect but should not rewrite without owner approval:

- `digital_twin_contexto_maestro.md`
- thesis material
- strategic roadmap material
- root context files before they are reviewed and classified
- documents containing personal, academic, business, or publication strategy

Codex must not:

- move or rename documentation unless the ticket explicitly allows it
- convert root owner-decision files into public docs without approval
- mark a document deprecated unless a replacement or owner instruction exists
- rewrite strategic master context as if it were implementation detail
- create duplicate canonical documents for the same policy

## 12. Public and Private Documentation Policy

The repository is currently treated as public. Documentation should be classified before commit.

Safe-to-public by default:

- repository structure contracts
- generated/runtime artifact policy
- source tree policy
- clean-clone validation reports
- build and launch workflow docs that do not expose secrets
- general USD and extension development conventions

Requires owner review:

- `digital_twin_contexto_maestro.md`
- root `00_*.txt` to `07_*.txt` context files
- thesis notes
- research notes with unpublished conclusions
- roadmap files that reveal strategy, deadlines, partnerships, or academic plans
- screenshots, diagrams, or examples containing private project data

Should not be committed without explicit approval:

- secrets or credentials
- private paths that identify local machines or accounts unnecessarily
- unpublished thesis drafts intended to remain private
- private datasets
- vendor documents with unclear licensing
- copyrighted reference documents copied into the repo

## 13. Documentation Drift Controls

To reduce drift:

- maintain one active source-of-truth per topic
- keep `docs/README.md` current once created
- use ADRs for major accepted decisions
- update validation reports only by adding new reports, not by silently rewriting old evidence
- mark superseded analysis clearly instead of deleting useful history
- require future tickets that change structure to update the relevant contract in the same change
- include validation commands in documentation that describes build, launch, or repository hygiene

## 14. Open Decisions

The following decisions remain open:

1. Whether `digital_twin_contexto_maestro.md` should be committed, moved into `docs/research/`, moved into `docs/thesis/`, sanitized, or kept private.
2. Whether root context files `00_*.txt` to `07_*.txt` should be converted to Markdown and moved into `docs/`.
3. Whether `current_repository_analysis.md` should be archived, excluded, or replaced entirely by `current_repository_analysis_codex.md`.
4. Whether architecture reports and architecture contracts should remain together in `docs/architecture/` or be split later into `docs/architecture/analysis/` and `docs/architecture/contracts/`.
5. Whether thesis material belongs in this public repository at all.
6. Whether roadmap documents should be public or maintained privately until milestones stabilize.
7. Whether the project should standardize on English-only filenames for public docs while allowing Spanish prose where useful.
8. Whether clean-clone validation reports should remain under `docs/architecture/` for historical continuity or move to `docs/validation/`.

## 15. Risks

- Public repository risk: root context and master context files may contain strategic or thesis-sensitive content.
- Drift risk: multiple repository analysis documents can conflict unless one is marked canonical.
- Discovery risk: without `docs/README.md`, new contributors and Codex must infer the active document set.
- Archive risk: moving old analysis too early may hide useful migration history.
- Validation evidence risk: the original working copy must be synced with the clean-clone validation commit before local docs state fully matches repository history.
- Naming risk: current numbered and mixed-language root files are useful for humans but do not scale as long-term public documentation paths.

## 16. Recommended Future Tickets

Recommended follow-up tickets:

1. Create `docs/README.md` as the documentation index.
2. Review root context files and classify each as public, private, archive, or convert-to-docs.
3. Decide whether `digital_twin_contexto_maestro.md` belongs in the public repository.
4. Move validation reports into `docs/validation/` after an explicit migration ticket.
5. Convert `docs/07_USD_MODELING_CONVENTIONS.md` into `docs/design/usd_modeling_conventions.md` after confirming no external references rely on the current path.
6. Create an ADR index and first ADRs for accepted repository structure decisions.
