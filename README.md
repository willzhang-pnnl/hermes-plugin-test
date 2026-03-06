# hermes-plugin-test

A test project for the [HERMES](https://github.com/softwarepub/hermes) plugin for metadata publication.

## Overview

This repository demonstrates and tests the HERMES workflow for automated publication of research software with rich metadata, using:

- **[hermes-plugin-python](https://github.com/softwarepub/hermes-plugin-python)** — harvests metadata from `pyproject.toml`
- **hermes CFF plugin** — harvests metadata from `CITATION.cff`

## Project Structure

```
.
├── CITATION.cff              # Citation metadata (harvested by hermes cff plugin)
├── hermes.toml               # HERMES workflow configuration
├── pyproject.toml            # Python project metadata (harvested by hermes toml plugin)
├── src/
│   └── hermes_plugin_test/   # Minimal Python package
└── test/
    └── test_harvest.py       # Pytest tests for hermes metadata harvesting
```

## Getting Started

### Install dependencies

```bash
pip install -e ".[dev]"
```

### Run HERMES metadata harvest

```bash
hermes harvest
```

This reads metadata from `pyproject.toml` and `CITATION.cff` and writes the results to `.hermes/harvest/`.

### Run tests

```bash
pytest test/
```

## CI / CD

- **[ci.yml](.github/workflows/ci.yml)** — runs the pytest suite on every push and pull request.
- **[hermes.yml](.github/workflows/hermes.yml)** — runs `hermes harvest` on pushes to `main` to verify metadata publication works.
