# LOCAL MULTI-AGENT COMPUTER WORKER — PART 02

Production-oriented installer/deployment reference implementation for the Part 02 specification.

## Scope
Fresh install, update, repair, resumable downloads, SHA-256 and optional Ed25519 signatures, dependency resolution, runtime/model/browser/storage bootstrap, first-launch self-test, safe rollback and uninstall policies.

## Important deployment rule
All privileged or vendor-specific installation is driven by signed manifests. The code never downloads and executes an arbitrary shell script from an untrusted URL. For Ollama, the adapter supports an already-installed runtime and signed installer artifacts supplied by the deployment registry. Official Ollama distribution pages currently provide macOS/Windows installers and Linux installation instructions; a production registry should pin exact artifact URLs and hashes before shipping them. [Official download pages](https://ollama.com/download).

## Tests
`python -m pytest -q`

## Local demo
`python -m launcher --demo`
