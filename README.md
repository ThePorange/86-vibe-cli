# 86-vibe CLI

Implementation repository for the 86-vibe platform command-line interface.

## Status

This repository contains the IP-001-01 initial package skeleton. Only `version` and
`help` are implemented. Other approved command groups are registered as placeholders.

## Requirements

- Python 3.11 or newer
- pip

## Local Development

Create a virtual environment and install the package in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the CLI:

```bash
86vibe version
86vibe help
```

Run tests:

```bash
pytest
```

## Package Layout

```text
src/vibe/
├── cli/            Command-line interface (Typer)
├── configuration/  Configuration Service stub
├── logging/        Logging Service stub
├── bootstrap/      Bootstrap Service stub
└── version.py      Platform version metadata
```

## Architecture References

Implementation conforms to:

- AEP-002-02 Repository Directory Structure
- AEP-002-03 Python Package Architecture
- AEP-002-04 CLI Specification
- AEP-002-05 Configuration Management Specification
- AEP-002-06 Logging & Diagnostics Specification
- AEP-002-13 Build & Packaging Specification
- AEP-002-15 Local Development Workflow Specification
- ARP-002-01 CLI Service Interface Contract
- ARP-002-02 Configuration Service Interface Contract
- ARP-002-03 Logging Service Interface Contract
- ARP-002-09 Bootstrap Service Interface Contract

## Implementation Notes

- The installed command is `86vibe`.
- The Python distribution name is `vibe-cli`; the import package is `vibe`.
- Service stubs expose the public interfaces defined in ARP-002 without business logic.
- Placeholder commands exit with code `1` and report that they are not yet implemented.
- Version output uses conservative placeholder values until release automation is added.

## Next Steps

Future implementation increments should follow the sequence defined in AEP-002-04:

1. Implement `init`
2. Implement configuration loading and validation
3. Implement `doctor`
4. Add tests for each new command
