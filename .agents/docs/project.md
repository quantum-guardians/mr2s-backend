# Project Context

Fill this document during project initialization. Agents must verify commands against repository configuration before running them.

## Overview

- Product: MR2S simulation backend — an HTTP API that orients the edges of a
  weighted graph to minimize crowd-flow cost.
- Repository: https://github.com/quantum-guardians/mr2s-backend
- Primary users: the MR2S front ends (`mr2s-frontend`, `simulation-react`,
  `twin-world`, Unity `simulation`) that call the deployed API.
- Core domain: edge orientation over biconnected graphs — QUBO, simulated
  annealing, Robbins orientation, and brute force.
- Runtime environment: Python 3.11 (`Dockerfile`), FastAPI + uvicorn on port
  8000. Deployed at `https://quantum.yunseong.dev`.

## Architecture

- Entry points: `main.py` builds the FastAPI app, installs the CORS allowlist,
  and includes `optimization_v1_router` and `solver_v2_router`.
- Main modules: `router/` (HTTP layer), `dto/` (pydantic request/response
  models), `service/` (solver adapters and graph analysis), `domain/`
  (`weighted_graph.py`), `utils/` (`timeout.py`).
- Dependency direction: `router` depends on `dto` and `service`; `service`
  depends on `domain` and `mr2s-module`; `domain` depends on nothing local.
- External systems: `mr2s-module` (pinned to `0.1.7` in `requirements.txt`)
  provides the solvers; `networkx`/`numpy` support graph analysis.
- Persistent data: none. Every request is stateless.

## Commands

| Purpose | Command |
|---|---|
| Install dependencies | `python -m venv .venv && .venv/bin/pip install -r requirements.txt` |
| Run locally | `python main.py` (or `uvicorn main:app --reload`) |
| Format | TODO — none configured |
| Lint | TODO — none configured |
| Type-check | TODO — none configured |
| Unit tests | `python -m pytest` — `pytest==9.0.3` is installed but no test files exist yet |
| Integration tests | Manual request bodies in `docs/test.md` against a running server |
| Build | `docker build -t mr2s-backend .` |

## Constraints

- Supported platforms: Linux container (`python:3.11-slim`); process-based
  timeouts in `utils/timeout.py` keep this cross-platform.
- Compatibility requirements: `/api/v1` paths are frozen for existing clients;
  new solver work goes under `/api/v2/solvers`. `mr2s-module` is pinned —
  do not bump it without checking every solver response shape.
- Performance constraints: brute force is `O(2^|E|)`; keep it off any path a
  browser waits on and rely on the timeout wrapper.
- Security or privacy requirements: the CORS allowlist in `main.py` is
  explicit. Add an origin only when that front end is really deployed there.

## Ownership

- Maintainers: Yunseong <me@yunseong.dev>
- Sensitive modules: `main.py` (CORS allowlist), `utils/timeout.py`,
  `service/solver_catalog.py`
- Changes requiring explicit review: API path or response-shape changes,
  `mr2s-module` version bumps, timeout behavior.
