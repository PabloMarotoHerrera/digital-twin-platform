# Clean Clone Validation Report

Date: 2026-05-24

## 1. Summary

The GitHub baseline was validated from a clean clone at `C:\tmp\dt-clean-clone-validation\digital-twin-platform`.

Result: reproducible baseline validated.

- Clean clone succeeded from `https://github.com/PabloMarotoHerrera/digital-twin-platform.git`.
- Expected committed source and architecture documents were present.
- Forbidden/local artifacts were absent from the Git baseline before build.
- `repo.bat --help` bootstrapped successfully after allowing repo tooling access.
- `repo.bat build` completed successfully.
- `repo.bat launch my_own_software.kit` launched the app successfully, loaded the local product extensions, reached `app ready`, reached `RTX ready`, and exited cleanly.
- After validation, generated `_build`, `_repo`, and `_compiler` existed locally and were ignored by `.gitignore`.
- `git status --short` in the clone remained clean after build/launch.

## 2. Clone Path

```text
C:\tmp\dt-clean-clone-validation\digital-twin-platform
```

## 3. Commit Validated

```text
2bd1c983e61ee90a9fee717997cb9b003cdcd5c6
```

Recent history:

```text
2bd1c98 (HEAD -> main, origin/main, origin/HEAD) Initial platform architecture and source import
207208f Removing tools/containers folder, as the functionality was moved into `repo` instead (#136)
66f6e57 Merge pull request #134 from NVIDIA-Omniverse/109.0.3
8e3ddd8 KAT 109.0.3 release
0454edf Merge pull request #133 from NVIDIA-Omniverse/109.0.2
```

## 4. Git State Before Validation

Immediately after clone:

```powershell
git status --short
```

Output: empty.

Remotes:

```text
origin  https://github.com/PabloMarotoHerrera/digital-twin-platform.git (fetch)
origin  https://github.com/PabloMarotoHerrera/digital-twin-platform.git (push)
```

## 5. Source Existence Checks

Commands:

```powershell
Test-Path source/apps/my_own_software.kit
Test-Path source/extensions/custom.aec.modeling/config/extension.toml
Test-Path source/extensions/dt.energy.agent/config/extension.toml
Test-Path docs/architecture/current_repository_analysis_codex.md
```

Results:

```text
True
True
True
True
```

Conclusion: expected app, extension, and architecture source exists in the GitHub baseline.

## 6. Generated / Forbidden Artifact Checks Before Build

Commands:

```powershell
Test-Path _build
Test-Path _compiler
Test-Path _repo
Test-Path CustomPrimitiveMesh.zip
Test-Path source/apps/my_own_software.kit.before_extension_cleanup
Test-Path source/rendered_template_metadata.json
```

Results:

```text
False
False
False
False
False
False
```

Conclusion: generated/runtime/vendor/backup artifacts were absent from the committed baseline.

## 7. Commands Run

```powershell
git clone https://github.com/PabloMarotoHerrera/digital-twin-platform.git C:\tmp\dt-clean-clone-validation\digital-twin-platform
git status --short
git remote -v
git log --oneline --decorate -5
Test-Path source/apps/my_own_software.kit
Test-Path source/extensions/custom.aec.modeling/config/extension.toml
Test-Path source/extensions/dt.energy.agent/config/extension.toml
Test-Path docs/architecture/current_repository_analysis_codex.md
Test-Path _build
Test-Path _compiler
Test-Path _repo
Test-Path CustomPrimitiveMesh.zip
Test-Path source/apps/my_own_software.kit.before_extension_cleanup
Test-Path source/rendered_template_metadata.json
.\repo.bat --help
.\repo.bat launch --help
.\repo.bat build --help
.\repo.bat build
.\repo.bat launch my_own_software.kit --help
.\repo.bat launch my_own_software.kit
git status --short
Get-Process | Where-Object { $_.ProcessName -match 'kit|my_own|omni' }
git check-ignore -v _build/apps/exts.deps.generated.kit _repo/repo.log _compiler/current
git rev-parse HEAD
```

## 8. Repo Tooling Result

Initial non-escalated `repo.bat --help` failed with:

```text
Acceso denegado.
ModuleNotFoundError: No module named 'packmanapi'
```

After allowing repo tooling/bootstrap access, `repo.bat --help` succeeded and listed tools including:

- `build`
- `launch`
- `test`
- `package`
- `template`
- `pull_extensions`

The launch tool recognized the committed app:

```text
usage: repo launch [-h] [--container] [-p FROM_PACKAGE] [-n APP_NAME]
                   {my_own_software.kit} ...
```

App-specific launch help:

```text
usage: repo launch my_own_software.kit [-h] [--container]
```

## 9. Build / Prebuild Result

Command:

```powershell
.\repo.bat build
```

Result: success, exit code `0`.

Generated release outputs included:

- `_build/windows-x86_64/release/my_own_software.kit.bat`
- `_build/windows-x86_64/release/tests-custom.aec.modeling.bat`
- `_build/windows-x86_64/release/tests-dt.energy.agent.bat`
- `_build/windows-x86_64/release/exts/`
- `_build/windows-x86_64/release/extscache/`
- `_build/windows-x86_64/release/kit/`

`git status --short` remained clean after build because generated directories are ignored.

## 10. Launch Result

Command:

```powershell
.\repo.bat launch my_own_software.kit
```

Result: success, exit code `0`.

The app launched, loaded local extensions, reached ready state, and shut down cleanly. No Kit process remained after the command returned.

Key launch output:

```text
launching my_own_software.kit!
[4.606s] [ext: custom.aec.extrude-0.1.0] startup
[4.646s] [ext: custom.aec.primitive_mesh-0.1.0] startup
[7.695s] [ext: custom.aec.modeling-0.1.0] startup
[7.768s] [ext: custom.aec.sketch-0.1.0] startup
[7.791s] [ext: custom.aec.thermal_viz-0.1.0] startup
[7.906s] [ext: dt.energy.agent-0.1.0] startup
[10.331s] [ext: my_company.my_usd_composer_setup_extension-0.1.0] startup
[10.413s] [ext: my_own_software-0.1.0] startup
[10.664s] app ready
[16.919s] RTX ready
```

Log file:

```text
C:\Users\pablo\.nvidia-omniverse\logs\Kit\My Own Software\0.1\kit_20260524_105021.log
```

The log tail showed orderly plugin shutdown at approximately `173.970s`.

## 11. Warnings Observed

Warnings at startup:

```text
[Warning] [omni.ext.plugin] [ext: CustomPrimitiveMesh] Extensions config 'extension.toml' doesn't exist ...
[Warning] [omni.ext.plugin] [ext: Custom.kit.primitive.mesh] Extensions config 'extension.toml' doesn't exist ...
```

Likely cause:

- Local user Kit config references old/uncommitted extension search paths under the user profile:
  `C:/Users/pablo/AppData/Local/ov/data/Kit/My Own Software/0.1/exts/3/...`
- This does not appear to come from the Git baseline because `CustomPrimitiveMesh.zip` and old primitive extension artifacts are absent from the clean clone.
- The app still launched and loaded the committed product extensions.

Other environment warning:

```text
Ignoring proxy 'localhost:8891' from omniverse.toml. This is a stale configuration from omniverse cache v1.
```

Likely cause:

- User-level Omniverse cache/config, not repository baseline.

Performance warning:

```text
Client rtx.raytracing.plugin has acquired [carb::settings::ISettings v1.1] 100 times...
```

Likely cause:

- Runtime/Kit performance warning. Not a baseline reproducibility blocker.

## 12. Generated State After Validation

After build/launch:

```powershell
Test-Path _build
Test-Path _compiler
Test-Path _repo
```

Results:

```text
True
True
True
```

Ignore validation:

```text
.gitignore:2:_build/    _build/apps/exts.deps.generated.kit
.gitignore:4:_repo/     _repo/repo.log
.gitignore:3:_compiler/ _compiler/current
```

Final clone status before writing this report:

```powershell
git status --short
```

Output: empty.

After writing this report in the clean clone, `docs/architecture/clean_clone_validation_report.md` is an uncommitted local validation artifact.

## 13. Missing Files Discovered

No missing committed source files were discovered.

The clean clone baseline contains:

- app descriptor
- local extension source
- setup extension assets/materials/layouts
- docs required by prior tickets
- Kit template tooling and templates

The intentionally excluded local files were absent:

- `CustomPrimitiveMesh.zip`
- `source/apps/my_own_software.kit.before_extension_cleanup`
- `source/rendered_template_metadata.json`
- generated tree dumps

## 14. Reproducibility Verdict

The GitHub baseline is reproducible on this validation machine.

Validated:

- clean clone
- repo tooling bootstrap
- dependency/build generation
- app discovery by repo launch tooling
- app startup
- local extension discovery and startup
- RTX readiness
- clean generated state under Git ignore policy

The only warnings observed appear tied to user-level Omniverse configuration, not missing committed repository files.

## 15. Recommended Fixes / Next Ticket

Recommended next ticket: user-local configuration hygiene and optional automated smoke test.

Suggested scope:

- Inspect user-level Kit config that references stale `CustomPrimitiveMesh` and `Custom.kit.primitive.mesh` extension paths.
- Decide whether to document how to reset/clean user Kit extension search paths for `My Own Software`.
- Add a repeatable no-window smoke test command if the Kit app supports passing app args through `repo launch` or generated `.bat` scripts.
- Optionally run generated extension test scripts after the launch baseline is accepted.

Do not change product source as part of that diagnostic unless a repository-owned cause is found.
