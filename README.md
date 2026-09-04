# Complete the Scribble v2.0.35 Samsung GitHub Promotion

You are operating inside a Samsung-connected Windows environment with Gemini CLI. Continue and complete the interrupted Scribble v2.0.35 release promotion from the public development repository to Samsung GitHub. Perform the work, verify it end to end, and report the actual outcome. Do not merely describe the steps.

The previous attempt stopped safely. It found two blockers:

1. Internal `main` contains Samsung-only CI/CD and Inno Setup commits, so pushing the public release commit directly would be a non-fast-forward update.
2. The Samsung GitHub credential lacks the `workflow` scope required to introduce commits that modify `.github/workflows/build.yml`.

Preserve every internal commit and customization. Integrate the public release through a normal merge commit. Never force-push or rewrite history.

## Known release information

- Public repository: `https://github.com/datap0nd/scribble.git`
- Samsung repository: `https://github.sec.samsung.net/r-cunha/scribble.git`
- Samsung GitHub CLI repository: `github.sec.samsung.net/r-cunha/scribble`
- Stable tag: `v2.0.35`
- Exact public release commit: `2c238704aa312b03cd0fb6a6c95c150b7d7692bd`
- Required release asset: `ScribbleSetup.exe`
- Expected public installer SHA-256: `C95A3CB2AE29E82640A27982C41FB7534800C044BB21B85622F4D3B5A5EC00BF`
- Exact updater URL embedded in all five Scribble integrations: `https://github.sec.samsung.net/r-cunha/scribble/releases/latest/download/ScribbleSetup.exe`

Scribble has five integrations: Chrome, Outlook, Excel, PowerPoint, and Word. They share one installer and one updater URL.

## Safety requirements

- Never expose, print, request, or store a personal access token in files, prompts, command arguments, or logs.
- Use the existing GitHub CLI credential store and interactive browser or device authorization.
- Never use `git push --mirror`, `--force`, `--force-with-lease`, reset, rebase, history rewriting, branch deletion, tag deletion, or release deletion.
- Never discard or overwrite Samsung-only commits, workflows, build configuration, or Inno Setup customizations.
- Do not rebuild or modify the public installer. Promote the exact public release asset.
- Do not manufacture the release from `continuous`, a prerelease, a draft, an untagged commit, or `v2.0.34`.
- Do not overwrite an existing release or release asset. If partial state exists from the previous attempt, inspect and verify it before continuing.
- Stop on an ambiguous merge conflict, tag mismatch, asset hash mismatch, authentication failure, or unexpected remote state. Report the exact blocker instead of bypassing it.
- Do not claim automatic updates are ready unless the final unauthenticated download test succeeds.

## Procedure

### 1. Refresh Samsung GitHub authorization

Run:

```powershell
gh auth refresh --hostname github.sec.samsung.net --scopes workflow
gh auth setup-git --hostname github.sec.samsung.net
gh auth status --hostname github.sec.samsung.net
```

Allow me to complete any interactive browser or device authorization. Confirm that authentication succeeds and includes the `workflow` scope without printing credentials.

### 2. Create a clean temporary workspace

Do not alter an unrelated checkout. Create a clean clone beneath the operating-system temporary directory:

```powershell
$workRoot = Join-Path ([IO.Path]::GetTempPath()) ("scribble-internal-promotion-" + [Guid]::NewGuid().ToString("N"))
git clone https://github.com/datap0nd/scribble.git $workRoot
Set-Location $workRoot
git remote add samsung https://github.sec.samsung.net/r-cunha/scribble.git
git fetch --prune origin
git fetch --prune samsung
git fetch --tags origin
```

### 3. Revalidate the public stable release

Before changing Samsung GitHub, verify all of the following:

- Public tag `v2.0.35` exists.
- The peeled tag resolves exactly to commit `2c238704aa312b03cd0fb6a6c95c150b7d7692bd`.
- The public GitHub Release for `v2.0.35` is published, non-draft, and non-prerelease.
- The release contains an asset named exactly `ScribbleSetup.exe`.
- The tagged `src/Scribble/Utilities/SelfUpdater.cs` contains the exact Samsung updater URL listed above.
- The downloaded public asset begins with the Windows `MZ` header.
- Its SHA-256 is exactly `C95A3CB2AE29E82640A27982C41FB7534800C044BB21B85622F4D3B5A5EC00BF`.

Download the asset to the temporary workspace using the public GitHub Release. Do not rebuild it.

### 4. Inspect the current internal state

Fetch Samsung GitHub again and record:

- current `samsung/main` commit;
- whether internal tag `v2.0.35` already exists and its peeled commit;
- whether an internal `v2.0.35` Release exists;
- whether `ScribbleSetup.exe` is already attached.

Treat a partially completed state idempotently:

- If internal tag `v2.0.35` exists and resolves to the exact public commit, keep it.
- If it resolves anywhere else, stop. Do not delete or move the tag.
- If the internal release or asset already exists, verify it rather than overwriting it.
- If an existing asset hash differs from the expected public hash, stop.

### 5. Integrate the public release without rewriting internal history

Create a local integration branch starting from the current internal `main`:

```powershell
git switch --create stable-promotion samsung/main
git merge --no-ff 2c238704aa312b03cd0fb6a6c95c150b7d7692bd
```

The resulting history must retain the complete internal `main` history and include the exact public v2.0.35 commit as an ancestor.

Preserve Samsung-only CI/CD, workflow, and Inno Setup customizations when resolving conflicts. Preserve the public v2.0.35 application changes and embedded Samsung updater URL. If a conflict is ambiguous or preserving one side would discard meaningful work from the other, stop and show me the exact conflicting files and differences instead of guessing.

After resolving any clear conflicts, run appropriate repository tests and build validation. Confirm all of the following before pushing:

- the integration branch descends from the previous `samsung/main` commit;
- public commit `2c238704aa312b03cd0fb6a6c95c150b7d7692bd` is an ancestor of the integration branch;
- internal-only changes remain present;
- the updater URL is still the exact Samsung URL;
- the working tree is clean;
- the push from the integration branch to internal `main` will be a normal fast-forward of internal `main`.

Push without force:

```powershell
git push samsung stable-promotion:main
```

### 6. Create or verify the internal tag

Internal tag `v2.0.35` must point to the exact public release commit, not the new internal merge commit.

If the tag does not yet exist internally, push the exact public tag normally. If it already exists at the correct commit, leave it unchanged. Never retag, delete, or force-update it.

Verify the remote peeled tag resolves to:

```text
2c238704aa312b03cd0fb6a6c95c150b7d7692bd
```

### 7. Create the internal release and upload the exact installer

Create a published, non-draft, non-prerelease Samsung GitHub Release for `v2.0.35` if one does not already exist. Give it the title `Scribble v2.0.35` and appropriate stable release notes.

Upload the already verified public `ScribbleSetup.exe`. Do not rebuild, rename, transform, or overwrite it. If the release or asset already exists, verify the existing object and continue only when it matches.

Ensure the internal release is marked Latest and has exactly one relevant installer asset named `ScribbleSetup.exe`.

### 8. Verify authenticated and unauthenticated downloads

Download the internal asset once through authenticated GitHub CLI access. Verify:

- filename is `ScribbleSetup.exe`;
- it begins with `MZ`;
- SHA-256 equals `C95A3CB2AE29E82640A27982C41FB7534800C044BB21B85622F4D3B5A5EC00BF`.

Then test this exact updater URL with a fresh HTTP request that sends no `Authorization` header, cookies, browser session, manually supplied token, or interactive SSO:

```text
https://github.sec.samsung.net/r-cunha/scribble/releases/latest/download/ScribbleSetup.exe
```

Verify the response is the executable itself, not HTML or a login page. It must begin with `MZ` and have the same expected SHA-256.

If the unauthenticated request redirects to login, returns HTML, receives `401` or `403`, or otherwise cannot retrieve the executable directly, state clearly that the source and release were promoted but automatic updates remain blocked by Samsung GitHub authentication. Do not weaken repository access or invent credentials. Recommend an approved internal artifact endpoint that permits direct device downloads, or a deliberately designed authenticated updater.

### 9. Clean up safely

Remove only the temporary clone created during this run, and only after verifying its resolved absolute path remains beneath the operating-system temporary directory. Never delete a broad directory or another checkout.

## Required final report

Return a concise report containing:

- promoted tag;
- previous internal `main` commit;
- resulting internal merge commit;
- exact public commit;
- confirmation that both histories were preserved;
- public installer SHA-256;
- authenticated internal download SHA-256;
- unauthenticated updater download SHA-256;
- internal Release URL;
- exact updater URL;
- whether automatic updates are fully ready across all five apps;
- any remaining blocker and its precise next action.

Success requires all of the following:

1. Internal `main` preserves its prior history and contains the public v2.0.35 commit.
2. Internal tag `v2.0.35` points exactly to the public release commit.
3. The internal Release contains the exact verified public installer.
4. The updater URL downloads that installer without browser state or credentials.
