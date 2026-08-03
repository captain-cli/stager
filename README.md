# Captain Stager

**Stager** is a standalone Captain tool that prepares directories and seed files from a declarative JSON loading manifest.

It remains independent from Omni Shell. Omni can download, register, and invoke it as an external module, while the same executable remains usable from a terminal, CI pipeline, deployment script, or another Captain host.

## Commands

```bash
stager validate manifests/omni-fs.json
stager inspect manifests/omni-fs.json
stager plan manifests/omni-fs.json
stager apply manifests/omni-fs.json
stager apply manifests/omni-fs.json --root ./runtime/omni-fs
stager apply manifests/omni-fs.json --dry-run
```

Machine-readable output for Omni Shell:

```bash
stager plan manifests/omni-fs.json --output json
stager apply manifests/omni-fs.json --root ./runtime/omni-fs --output json
```

## Install for development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Responsibilities

Stager owns manifest loading, validation, variable substitution, safe root-relative path resolution, planning, dry runs, directory creation, seed-file creation, and structured results.

Stager does not own Omni application state, filesystem browsing, permissions, package downloads, registry discovery, or long-running services.

See `integrations/omni-shell/README.md` for the host adapter and application registration starter.
