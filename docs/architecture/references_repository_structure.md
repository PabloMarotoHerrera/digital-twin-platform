# References Repository Structure Contract

Status: proposed architecture contract  
Scope: future root `references/` structure only  
Date: 2026-05-24

## 1. Executive Summary

This repository does not currently have a root-level `references/`, `third_party/`, or `vendor/`
directory. Existing reference-like material is distributed across:

- `README.md`, with NVIDIA Omniverse, Kit SDK, NGC, DLI, Docker, Git LFS, Visual Studio, and
  Omniverse license links.
- `readme-assets/`, with Kit App Template images and additional docs inherited from the NVIDIA
  template.
- `templates/`, with NVIDIA template documentation, examples, template assets, and links.
- `docs/architecture/`, with project architecture contracts that mention EnergyPlus, OpenUSD,
  Omniverse Kit, vendor policy, data policy, and future artifact boundaries.
- root owner-decision files, which may include strategic references but are not yet organized.
- `CustomPrimitiveMesh.zip`, an untracked archive that requires owner/license review before any
  commit or relocation decision.

Future root `references/` should be a structured inventory of external-resource metadata: links,
citations, standards pointers, vendor documentation pointers, manual metadata, license notes, and
download instructions. It should not become a hidden vendor folder or a place to commit copyrighted
manuals, PDFs, datasets, binaries, examples, or external source archives.

This document is a design contract only. It does not create `references/`, download references,
vendor external documents, move files, edit source, stage, commit, or push.

## 2. Current Reference-Like Material

Current observed reference-like artifacts:

| Path or area | Current role | Notes |
| --- | --- | --- |
| `README.md` | Template/project README with external links | Contains NVIDIA/Omniverse/Kit SDK/NGC/DLI/Docker/Git/VS Code/License links |
| `readme-assets/` | Template README assets and additional docs | Local documentation and images inherited from Kit App Template |
| `readme-assets/additional-docs/` | Supplementary Kit App Template docs | Troubleshooting, streaming, tooling, Windows setup, data collection |
| `templates/` | Kit scaffold templates | Contains template docs, source, assets, license headers, external links |
| `docs/07_USD_MODELING_CONVENTIONS.md` | Internal USD/AEC convention contract | Not an external reference, but may cite future OpenUSD/AEC references |
| `docs/architecture/*.md` | Architecture contracts | Mention EnergyPlus, OpenUSD, Omniverse, vendor/data/artifact boundaries |
| root `00_*.txt` files | Owner-decision/project context notes | Not yet classified into public docs or references |
| `digital_twin_contexto_maestro.md` | Owner-review strategic note | Public/private decision required before organizing |
| `current_repository_analysis.md` | Earlier analysis input | Not source-of-truth; archive/owner decision |
| `CustomPrimitiveMesh.zip` | Untracked archive | Vendor/archive/unknown; do not commit without owner and license approval |
| `EnergyPlusV24-2-0/` | Not present in this working copy | If added later, classify as vendor/external or local install, not references |
| `_build/.../PACKAGE-LICENSES/*.md` | Generated package license files | Generated build artifacts, not reference source |

No local `.pdf`, `.bib`, `.ris`, `.url`, or `.webloc` reference files were found by the validation
commands used for this ticket.

## 3. Architectural Role of Future `references/`

Future root `references/` should contain structured metadata about external resources that inform
the project but are not project source, datasets, examples, tests, or vendored dependencies.

Use `references/` for:

- curated external documentation links
- standards references
- vendor documentation pointers
- manuals metadata
- citation lists
- DOI, arXiv, URL, and publication metadata
- license notes for external resources
- external asset pointers
- download instructions when local copies are not committed
- checksum manifests for approved external downloads, if needed

Do not use `references/` for:

- copied copyrighted PDFs or manuals unless redistribution is explicitly allowed
- external source code
- vendor binaries
- EnergyPlus installs
- EPW/weather libraries
- datasets
- runnable examples
- test fixtures
- generated outputs
- templates inherited from Kit App Template
- readme images/assets
- private thesis notes or strategy notes without approval
- local browser exports, random URL dumps, or unreviewed bookmarks

The short rule is: `references/` contains pointers and metadata, not payloads.

## 4. Proposed Future Layout

When `references/` is eventually created by a future ticket, the recommended structure is:

```text
references/
  README.md
  links/
  standards/
  vendor_docs/
  papers/
  manuals/
  citations/
  licenses/
  external_assets/
```

### `references/README.md`

Index explaining reference categories, public-repo rules, metadata format, licensing policy, and
how references relate to docs, data, examples, vendor resources, and external artifact storage.

### `references/links/`

Curated link inventories for web resources that are useful but not formal standards, manuals, or
papers. Entries should include topic, owner, access date, and why the link matters.

### `references/standards/`

Pointers to standards and specifications, such as OpenUSD documentation/specs, building-energy
standards, file-format specs, and interoperability references. Actual standards documents should
not be committed unless redistribution is clearly permitted.

### `references/vendor_docs/`

Vendor documentation pointers for NVIDIA Omniverse Kit, Kit App Template, OpenUSD-related NVIDIA
docs, EnergyPlus documentation, and other tool/vendor documentation. Prefer URLs and metadata over
local copies.

### `references/papers/`

Research paper metadata: title, authors, DOI, arXiv, URL, topic tags, short summaries, and relevance
notes. PDFs require explicit license and owner approval.

### `references/manuals/`

Manual metadata and download/source pointers. Manuals should normally be linked, not copied. If a
local copy is approved, this folder may contain metadata that points to an artifact store or
approved local path.

### `references/citations/`

Optional BibTeX, CSL JSON, or citation index files if the project starts producing thesis or paper
outputs. Citation files should be reviewed for public/private suitability.

### `references/licenses/`

License notes and redistribution decisions for external resources. This is not a replacement for
the root `LICENSE` or generated package licenses.

### `references/external_assets/`

Metadata for external assets such as sample models, vendor examples, weather libraries, material
libraries, or image assets. The actual assets belong in `data/`, `examples/`, external artifact
storage, `vendor/`, or `third_party/` only after separate approval.

## 5. Boundary Policy

### `references/` vs `docs/references/`

`docs/references/` may contain narrative curated reference pages that are meant to be read as
documentation. Root `references/` should contain structured inventories and metadata. A future
`docs/references/README.md` can link to root `references/` inventories.

### `references/` vs `docs/research/`

`docs/research/` is for analysis, interpretation, experiments, thesis notes, and synthesis.
`references/` is for the external-resource metadata that supports that research. Do not place
private thesis strategy or sensitive research notes in public `references/` without owner approval.

### `references/` vs `data/`

`data/` is for approved, curated input datasets. `references/` may contain dataset citations,
licenses, source URLs, and download notes. Weather/EPW libraries, telemetry datasets, and measured
building data are data/artifact concerns, not references by default.

### `references/` vs `examples/`

`examples/` is for runnable or loadable sample workflows/assets. `references/` can point to external
example projects or vendor tutorials, but should not copy them into the repo.

### `references/` vs `third_party/` or `vendor/`

`references/` contains pointers and metadata. `third_party/` or `vendor/` would contain actual
external code/assets/binaries if a future ticket explicitly approves vendoring. References must not
be used as a workaround to commit third-party payloads without license review.

### `references/` vs `templates/`

`templates/` is Kit App Template scaffold source. It already contains docs, assets, and examples
needed by the template workflow. Do not duplicate template docs into `references/`.

### `references/` vs `readme-assets/`

`readme-assets/` supports the root README and inherited template docs. It is not a general reference
library. Do not move README support images/docs into `references/` unless a future documentation
restructure explicitly changes README ownership.

## 6. Licensing and Copyright Policy

Because this repository is public, references policy must be conservative:

- Prefer links, citations, summaries, and metadata over copied files.
- Do not commit copyrighted PDFs, manuals, standards, books, course material, screenshots, or
  vendor documentation unless license terms explicitly allow redistribution.
- Do not copy NVIDIA, EnergyPlus, standards-body, or vendor documentation wholesale.
- Record license/source information for each committed reference entry.
- Record access dates for external links.
- Keep summaries short and original; do not paste long copyrighted excerpts.
- Treat unclear redistribution rights as "do not commit local copy."
- Use external artifact storage or private notes for approved but non-public resources.
- Do not commit proprietary assets, client materials, private building data, or licensed vendor
  examples without explicit owner approval.

## 7. EnergyPlus Reference Policy

EnergyPlus references may include:

- official EnergyPlus documentation links
- installation guide links
- IDD/IDF documentation links
- weather/EPW catalog links
- version notes
- license/provenance notes
- download instructions or checksums for approved workflows

EnergyPlus references must not include by default:

- EnergyPlus binaries or install directories
- copied manuals without license review
- EPW/weather libraries
- generated IDF/ESO/SQL/CSV outputs
- copied example datasets unless license, size, and purpose are approved

If `EnergyPlusV24-2-0/` appears later, it should be classified as vendor/external or local install,
not as `references/`.

## 8. NVIDIA, Omniverse, Kit, and OpenUSD Reference Policy

NVIDIA/Omniverse/OpenUSD references may include:

- NVIDIA docs links
- Kit App Template docs links
- Omniverse Kit SDK manual links
- Kit extension API documentation links
- OpenUSD documentation/specification links
- NGC/NVCF/DGX Cloud documentation links
- license and product-specific terms links
- notes about validated Kit/App Template versions

Policy:

- Do not copy proprietary NVIDIA docs wholesale.
- Preserve NVIDIA license headers in inherited template/source files.
- Template assets remain in `templates/`, `source/`, or `readme-assets/` as appropriate.
- Root `references/` may index official links and version notes, not duplicate template payloads.
- App `.kit` URLs to Omniverse material/environment S3 resources are app configuration references,
  not `references/` contents.

## 9. Paper and Research Reference Policy

Research references should be handled as metadata-first:

- Use DOI, arXiv, publisher URL, official project URL, or citation metadata.
- BibTeX is optional and should be introduced only if thesis/publication workflows need it.
- Short summaries are allowed when written in original wording.
- PDFs require license and owner approval before commit.
- Sensitive thesis notes, strategy, unpublished analysis, or private research planning should live
  in `docs/research/` or private storage only after owner decision, not automatically in public
  `references/`.

## 10. Reference Metadata Policy

Each future reference entry should include enough metadata to make it auditable:

```text
title
url
source
license
access_date
topic
summary
local_copy_allowed
local_copy_path
notes
```

Recommended optional fields:

```text
version
publisher
authors
doi
arxiv
checksum
retrieved_by
related_docs
related_code
public_safe
owner_review
```

Metadata files should use Markdown, YAML, TOML, JSON, BibTeX, or CSL JSON only after the format is
chosen deliberately. Avoid ad hoc browser bookmark dumps.

## 11. Update and Staleness Policy

References can rot or become misleading. Future reference entries should include:

- `access_date`
- version or release channel when applicable
- vendor/API version notes
- status: active, stale, superseded, deprecated, or owner-review
- last review date
- replacement link when superseded

Do not auto-update references without review. Link updates can change technical meaning, licensing,
or public/private suitability.

## 12. Codex Access Policy

Codex may add or edit references only when a ticket explicitly allows reference changes.

Required behavior:

- Do not download or vendor copyrighted material.
- Do not commit PDFs/manuals unless explicitly approved.
- Include source, license, and access date when adding references.
- Do not invent citations, DOIs, URLs, or paper metadata.
- Use official/vendor sources where possible.
- Summarize references in original wording and avoid long copied excerpts.
- Flag license uncertainty instead of guessing.
- Treat public-repo copyright/licensing as high risk.
- Do not move strategic owner-decision notes into public references without owner approval.

## 13. Current Artifact Classification

| Artifact | Classification | Recommendation |
| --- | --- | --- |
| `README.md` external links | Existing project/template documentation | Stay in README; future reference index may cite major official links |
| `readme-assets/` | README support assets and template docs | Stay where it is; not root references |
| `readme-assets/additional-docs/*.md` | Inherited Kit App Template docs | Stay where they are unless future docs restructure says otherwise |
| `templates/` | Kit template/scaffolding | Stay where it is; not references |
| template README/docs links | Template-local documentation references | Stay template-local |
| NVIDIA license headers in source/templates | Source/template license metadata | Preserve in place |
| `docs/07_USD_MODELING_CONVENTIONS.md` | Internal convention contract | Stay in docs; may link to future OpenUSD/AEC reference index |
| `docs/architecture/*.md` external mentions | Architecture contracts | Stay in docs; may cite future root references later |
| root `00_*.txt` files | Owner-decision context/workflow notes | Owner review required; not automatically references |
| `digital_twin_contexto_maestro.md` | Strategic owner-review note | Owner review required; likely docs/research/private decision, not references by default |
| `current_repository_analysis.md` | Earlier analysis input | Archive/owner decision; not canonical references |
| `CustomPrimitiveMesh.zip` | Untracked archive/vendor/unknown | Do not commit; owner/license review required; possible vendor/third_party or ignore decision later |
| `EnergyPlusV24-2-0/` | Not present | If introduced, classify as vendor/external/local install, not references |
| `_build/.../PACKAGE-LICENSES/*.md` | Generated package license outputs | Generated artifacts; do not commit as references |
| App `.kit` S3 material/environment URLs | Runtime/app configuration references | Keep in app config; do not mirror into references unless documenting provenance |
| External links in source comments/config | Source/config metadata | Keep in source; future reference index may cite official docs only |

## 14. Open Decisions

- Whether to create root `references/` or keep all references under future `docs/references/`.
- Whether references should be plain Markdown, YAML/TOML metadata, BibTeX, CSL JSON, or a mix.
- Whether to allow any local PDF/manual copies in this public repo.
- Whether to introduce `third_party/` or `vendor/` for approved external payloads.
- Whether EnergyPlus manuals/examples/weather catalogs should be links only or backed by an
  artifact-store manifest.
- Whether NVIDIA/Omniverse official docs should be centrally indexed or left in README/template docs.
- Whether thesis/publication references should live in this public repo.
- Whether `CustomPrimitiveMesh.zip` is source, vendor, archive, example, or should be ignored.
- How often references should be reviewed for stale links.

## 15. Risks

- Public-repo copyright violations from copied manuals, PDFs, screenshots, standards, or vendor docs.
- Accidentally turning `references/` into a vendor folder.
- Confusing references with data, examples, or tests.
- Stale external links causing outdated engineering decisions.
- License ambiguity around EnergyPlus examples, EPW weather files, NVIDIA assets, or third-party
  sample models.
- Root owner-decision files may contain sensitive strategy or private context unsuitable for public
  references.
- `CustomPrimitiveMesh.zip` could be committed without provenance if not handled deliberately.
- Centralizing references too early can create maintenance overhead before the project has stable
  research and external-resource workflows.

## 16. Validation Commands Used for This Contract

Read-only commands used while preparing this document:

```powershell
git status --short
Test-Path references
Test-Path third_party
Test-Path vendor
Get-ChildItem -Recurse -File -Force | Where-Object { $_.Extension -match "\.(pdf|bib|ris|zip|url|webloc|html|md|txt)$" } | Select-Object FullName,Length
rg -n "http|https|doi|arxiv|NVIDIA|Omniverse|OpenUSD|USD|EnergyPlus|manual|reference|license|copyright|paper|citation|BibTeX|vendor|third_party" docs README.md readme-assets templates source
Get-ChildItem readme-assets -Recurse -Force | Select-Object FullName,Mode,Length
Get-ChildItem -Force | Where-Object { $_.Name -match "EnergyPlus|CustomPrimitiveMesh|reference|manual|pdf|zip|third_party|vendor" } | Select-Object FullName,Mode,Length
Test-Path EnergyPlusV24-2-0
Get-ChildItem -Recurse -File -Force -Include *.pdf,*.bib,*.ris,*.url,*.webloc -ErrorAction SilentlyContinue | Select-Object FullName,Length
Get-Content README.md | Select-Object -First 320
rg -n "EnergyPlus|OpenUSD|Omniverse|NVIDIA|license|copyright|reference|manual|paper|citation|doi|arxiv|vendor|third_party|CustomPrimitiveMesh" docs README.md readme-assets source templates
```

## 17. Recommended Next Ticket

Recommended next ticket: design the future `config/` repository structure, because external
references, schemas, backend execution, EnergyPlus local configuration, and public/private policy
all intersect around committed examples versus local-only settings.
