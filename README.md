# Promote Scribble to Samsung GitHub

You are operating inside a Samsung-connected Windows environment with Gemini CLI. Complete the stable Scribble release promotion from the public development repository to Samsung GitHub. Do the work, verify it end to end, and report the outcome. Do not merely describe the steps.

## Objective

Promote the first approved stable Scribble release built from public commit `cbdf5f27b7ecc58c10dfbab33e9700453f3b991c` or a later descendant. The expected first eligible tag is `v2.0.35`.

Use these locations exactly:

- Public repository: `https://github.com/datap0nd/scribble.git`
- Samsung repository: `https://github.sec.samsung.net/r-cunha/scribble.git`
- Samsung GitHub CLI repository: `github.sec.samsung.net/r-cunha/scribble`
- Required release asset name: `ScribbleSetup.exe`
- Updater URL embedded in all five Scribble integrations: `https://github.sec.samsung.net/r-cunha/scribble/releases/latest/download/ScribbleSetup.exe`
- Promotion script: `scripts/Promote-StableRelease.ps1`

Scribble has five integrations: Chrome, Outlook, Excel, PowerPoint, and Word. They share one installer and one updater URL.

## Safety requirements

- Never expose, print, request, or store a personal access token in files, prompts, command arguments, or logs.
- Use the existing GitHub CLI credential store. If Samsung GitHub is not authenticated, run `gh auth login --hostname github.sec.samsung.net` interactively and let me complete the browser or device authorization. Then run `gh auth setup-git --hostname github.sec.samsung.net`.
- Do not use `git push --mirror`, `--force`, `--force-with-lease`, history rewriting, branch deletion, tag deletion, or release deletion.
- Do not overwrite an existing internal release or replace an existing release asset.
- Do not promote `continuous`, a draft, a prerelease, an untagged commit, or `v2.0.34`. The `v2.0.34` installer still points to public GitHub.
- Preserve all unrelated files and working-tree changes.
- Stop on authentication errors, ambiguous repository state, a non-fast-forward push, a mismatched hash, a missing asset, or any unexpected tag target. Explain the exact blocker instead of bypassing it.
- Do not claim automatic updates are ready unless the final unauthenticated download test succeeds.

## Procedure

1. Confirm the environment can reach both `github.com` and `github.sec.samsung.net`, and confirm `git`, `gh`, and Windows PowerShell 5.1 or newer are installed.

2. Confirm Samsung GitHub authentication without revealing credentials:

   ```powershell
   gh auth status --hostname github.sec.samsung.net
   ```

   If authentication is missing, perform the interactive login described above and then recheck it.

3. Work from a clean temporary clone of the public repository. Do not reuse or alter an unrelated checkout:

   ```powershell
   $workRoot = Join-Path ([IO.Path]::GetTempPath()) ("scribble-internal-promotion-" + [Guid]::NewGuid().ToString("N"))
   git clone https://github.com/datap0nd/scribble.git $workRoot
   Set-Location $workRoot
   ```

4. Fetch tags and identify the requested stable release. Prefer `v2.0.35`. Verify all of the following before proceeding:

   - The tag exists in the public repository.
   - It resolves to commit `cbdf5f27b7ecc58c10dfbab33e9700453f3b991c` or a descendant of that commit.
   - A published, non-draft, non-prerelease GitHub Release exists for the exact tag.
   - That public release contains an asset named exactly `ScribbleSetup.exe`.
   - The tagged `src/Scribble/Utilities/SelfUpdater.cs` contains the exact Samsung updater URL above.

   If `v2.0.35` does not yet exist as a completed public release, stop and report: `Create and finish the public v2.0.35 release before internal promotion.` Do not manufacture an internal release from `continuous` or from an older installer.

5. Update the local checkout to the latest public `main`, then inspect `scripts/Promote-StableRelease.ps1`. Use the repository script as the source of truth. Confirm it is unchanged from public `main` and that it:

   - selects the release by exact stable tag;
   - downloads the public release asset;
   - verifies the installer is a bounded Windows executable;
   - refuses tags whose source lacks the Samsung updater URL;
   - pushes only the approved tag commit to internal `main` and the exact stable tag;
   - creates the internal GitHub Release separately;
   - uploads `ScribbleSetup.exe`;
   - compares SHA-256 after authenticated and unauthenticated downloads;
   - refuses to overwrite an existing internal release.

6. Run the non-mutating preview first:

   ```powershell
   .\scripts\Promote-StableRelease.ps1 -Tag v2.0.35 -WhatIf
   ```

   Treat any warning or error as a blocker. Do not continue until the preview completes successfully and explicitly shows that the promotion operations would target `github.sec.samsung.net/r-cunha/scribble`.

7. Run the real promotion exactly once:

   ```powershell
   .\scripts\Promote-StableRelease.ps1 -Tag v2.0.35
   ```

   Allow the script to perform its guarded fast-forward push, create the internal Release, upload the installer, and execute its hash and direct-download checks. Do not substitute manual force pushes if the script stops.

8. Independently verify the final internal state:

   - Internal `main` resolves to the same commit as public tag `v2.0.35`.
   - Internal tag `v2.0.35` resolves to that same commit.
   - The internal Release is published, is marked Latest, and is neither draft nor prerelease.
   - The release contains exactly one relevant installer asset named `ScribbleSetup.exe`.
   - Download the asset once with `gh release download` and once from the updater URL with an HTTP request that sends no `Authorization` header, cookies, browser session, or interactive SSO.
   - Both downloaded files begin with the Windows `MZ` header and have the same SHA-256 as the public stable release asset.

9. If the unauthenticated updater URL redirects to login, returns HTML, receives `401` or `403`, or otherwise cannot download the executable directly, state clearly that the release was promoted but Scribble automatic updates are blocked by Samsung GitHub authentication. Do not weaken repository access or invent credentials. Recommend an approved internal artifact endpoint that permits direct device downloads, or an explicitly designed authenticated updater.

10. Remove only the temporary clone you created after verifying its resolved absolute path remains beneath the operating-system temporary directory. Never delete a broad directory or another checkout.

## Final report

Return a concise completion report containing:

- promoted tag;
- public and internal commit SHA;
- public installer SHA-256;
- authenticated internal download SHA-256;
- unauthenticated updater download SHA-256;
- internal Release URL;
- exact updater URL;
- whether automatic updates are fully ready across all five apps;
- any blocker and the precise next action.

Success means the approved stable source and tag are present internally, the internal Release contains the exact verified installer, and the updater URL downloads that installer without browser state or manually supplied credentials.
