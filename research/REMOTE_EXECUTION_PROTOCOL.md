# Remote Research Execution Protocol

## Resource and user-control guarantees
- Runner and child processes use Windows BelowNormal priority. This is a scheduling preference, not a hard CPU cap.
- Before each step, execution defers if total CPU load is at least 75% or available physical memory is below 25%.
- Status refreshes every 10 seconds during active checks and includes CPU load, available RAM, child PID, elapsed time, and current step.
- Controls (run from the Semplex repository):
  - `powershell -File .\scripts\research-control.ps1 status`
  - `powershell -File .\scripts\research-control.ps1 pause`
  - `powershell -File .\scripts\research-control.ps1 resume`
  - `powershell -File .\scripts\research-control.ps1 stop`
- Pause takes effect between checks; an active check finishes. Stop terminates the active child process tree.
- Do not launch a second runner while one is active.

## Workflow
Read artifacts/verification/latest.json and its referenced status.json. Use status heartbeats, not process/session listings, for progress. Inspect stdout and stderr logs for every failure. Missing exit marker is a failure, never a pass. Keep Agda checks sequential. Do not commit or push without explicit authorization.

## WSL invocation from PowerShell
Use `synesism/scripts/run_wsl_campaign_step.ps1` for Agda/WSL work. A direct PowerShell command embedding a long single-quoted `bash -lc '...'` payload can be parsed incorrectly by native argument handling; a superficial zero exit code is not sufficient evidence that the repository command ran. The wrapper base64-encodes the complete shell payload, executes it in the Ubuntu WSL repository path, and propagates the actual exit code. Its Diagnostic task has been verified to print the expected Synesism repository path. Every Agda campaign step must use this wrapper and inspect its own logs. The initial campaign `20261121-193516` used the unsafe direct invocation; its nominal Agda PASS statuses are invalid and must not be counted. Its Python/Lean steps and the milestone gate (which uses Python subprocess argument arrays) are separate and remain independently verifiable. Use `scripts/agda-corrected-campaign-plan.json` for the actual Agda rerun.

## Status meanings
RUNNING, WAITING_FOR_RESOURCES, PAUSED, PASS, FAIL, STOPPED, and ERROR have literal meanings. STOPPED is not full validation success.

## Research integrity
A syntax/typecheck is not a cross-language equivalence theorem. Distinguish proved, tested, proposed, and open claims. Do not use paid LinkedIn Actions.
