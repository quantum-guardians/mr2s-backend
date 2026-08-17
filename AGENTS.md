# Project Agent Instructions

## Scope and Precedence

This file is the repository-level entrypoint for coding agents.

Read `.agents/docs/project.md` before non-trivial work. Repository-specific
commands, constraints, and narrower instructions take precedence over these
template defaults.

## Project Workflow

For non-trivial work, follow:

- `.agents/docs/workflow.md`
- `.agents/docs/testing.md`

For tracked Git work, follow:

- `.agents/docs/issue.md`
- `.agents/docs/branch.md`
- `.agents/docs/commit.md`
- `.agents/docs/pull-request.md`

For published releases, follow:

- `.agents/docs/release.md`

Use project-local skills when installed and applicable. Skill instructions
define their own triggers, formats, and output paths.

## Project Structure & Module Organization

`main.py` builds the FastAPI app, applies the CORS allowlist, and includes the
routers. `router/` holds the HTTP layer (`optimization_v1_router.py`,
`solver_v2_router.py`), `dto/` the pydantic request and response models,
`service/` the solver adapters (`solver_catalog.py`,
`module_optimization_service.py`, `bruteforce_service.py`,
`edge_orientation_service.py`, `graph_analyzer.py`), `domain/` the
graph model (`weighted_graph.py`), and `utils/` shared helpers
(`timeout.py`). API documentation lives in `docs/api_spec.md`,
`docs/optimization_services.md`, and `docs/test.md`; keep `docs/api_spec.md`
in step with any route or payload change.

## API Versioning

`/api/v1` (`/mr2s`, `/raw-sa`, `/brute-force`) is maintained for existing
clients: one fixed solver per path, no options. New solver work belongs under
`/api/v2/solvers`, where `GET /api/v2/solvers` lists the catalog and
`POST /api/v2/solvers/{solver_name}` runs one with per-solver options. Do not
change v1 payload shapes; several deployed front ends still call them.

## Build, Test, and Development Commands

Create the environment with
`python -m venv .venv && .venv/bin/pip install -r requirements.txt`.
Run the server with `python main.py` (uvicorn on `0.0.0.0:8000`), or
`uvicorn main:app --reload` while iterating. Build the container with
`docker build -t mr2s-backend .`; CI publishes it to
`ghcr.io/quantum-guardians/mr2s` on every push to `main`.

`mr2s-module` is pinned to an exact version in `requirements.txt`. Solver
defaults and response shapes have changed between versions, so treat a bump as
a behavioral change: verify every solver path and update `docs/api_spec.md`
in the same pull request.

## Coding Style & Naming Conventions

Follow the existing style: 4-space indentation, `snake_case` for modules and
functions, `PascalCase` for pydantic models and classes, explicit type hints on
service and router signatures. Keep routers thin — validation in `dto/`,
computation in `service/`. New solvers register through
`service/solver_catalog.py` and implement `service/module_solver_protocol.py`
rather than adding a bespoke route. No formatter or linter is configured, so
match the surrounding file style closely.

## Testing Guidelines

`pytest` is a declared dependency but the repository has no test files yet. Add
them under a top-level `tests/` package mirroring the source layout, for
example `tests/service/test_solver_catalog.py`, and name tests
`test_<behavior>`. Use small deterministic graphs as fixtures. Until automated
coverage exists, exercise the request bodies in `docs/test.md` against a local
server and record the result in the pull request. Keep brute force off large
graphs: it is `O(2^|E|)` and the 28-edge sample in `docs/test.md` will time out.

## Commit & Pull Request Guidelines

History uses short imperative Conventional Commit subjects such as
`feat: add an /api/v2 solver catalog (raw-sa, qubo, robin)` and
`chore: upgrade mr2s-module 0.0.6 to 0.1.7`. Branch names follow
`<tag>/<issue num>`, for example `feature/32` or `fix/28`. Pull requests should
state the API-visible change, link the issue, list the endpoints exercised, and
include a sample request and response when a payload shape changes.

## Security & Configuration Tips

The CORS allowlist in `main.py` is explicit — add an origin only when that
front end is actually deployed there, and never widen it to `*`. Keep solver
credentials and endpoints out of source. Long-running solves must stay behind
`utils/timeout.py`, which uses processes rather than threads so a runaway solve
can be killed.
