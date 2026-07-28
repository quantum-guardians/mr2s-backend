# MR2S API Specification

## Base URL

```
http://localhost:8000
```

## Versions

| Version | Paths | Status |
|---------|-------|--------|
| v1 | `POST /api/v1/mr2s`, `POST /api/v1/raw-sa`, `POST /api/v1/brute-force` | Maintained for existing clients; fixed solver per path, no options |
| v2 | `GET /api/v2/solvers`, `POST /api/v2/solvers/{solver_name}` | Current. One path for every solver, with per-solver options |

## Common Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes (POST) | `application/json` |

---

## Endpoints

### 1. Health Check

```
GET /
```

**Response `200`**

```json
{
  "message": "Quantum Hackathon API"
}
```

---

### 2. List Solvers (v2)

```
GET /api/v2/solvers
```

Returns every solver the backend can run, together with the per-solver options it accepts. Drive the client's solver picker from this response instead of hardcoding names.

**Response `200`** — `SolverInfo[]`

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Canonical solver name, used as the path parameter |
| `description` | `string` | What the solver does |
| `options` | `string[]` | Option keys accepted in the request `options` object |
| `requires_dwave_credentials` | `bool` | `true` when the solver needs `DWAVE_API_TOKEN` (or `~/.config/dwave/dwave.conf`) |
| `aliases` | `string[]` | Alternative names accepted on the path |

**Example Response**

```json
[
  {
    "name": "raw-sa",
    "description": "Simulated annealing over graph metrics (APSP + flow), no QUBO.",
    "options": [
      "apsp_weight",
      "disconnected_pair_penalty",
      "flow_weight",
      "num_restarts",
      "random_seed",
      "sweeps_per_temperature"
    ],
    "requires_dwave_credentials": false,
    "aliases": ["sa"]
  },
  {
    "name": "qubo",
    "description": "Divide-and-conquer partitioning, subgraphs solved as QUBO with a local simulated annealing sampler.",
    "options": [],
    "requires_dwave_credentials": false,
    "aliases": ["dnc-qubo", "dnc-qubo-sa"]
  },
  {
    "name": "robin",
    "description": "Robbins orientation: a DFS pass that orients every edge at once. Deterministic and fast, but returns no edges when the graph has a bridge.",
    "options": [],
    "requires_dwave_credentials": false,
    "aliases": ["robbin"]
  }
]
```

---

### 3. Run a Solver (v2)

```
POST /api/v2/solvers/{solver_name}
```

Assigns a direction to every edge of an undirected graph using the named solver. Every solver shares one request and response schema.

**Path Parameters**

| Name | Type | Description |
|------|------|-------------|
| `solver_name` | `string` | Canonical solver name or alias — see [Solvers](#solvers) |

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `edges` | `EdgeRequest[]` | Yes | List of undirected edges with weights |
| `options` | `object` | No | Solver options; unknown keys are rejected with `400` |

**EdgeRequest**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `vertices` | `[int, int]` | Yes | Two vertex IDs (order does not matter) |
| `weight` | `int` | Yes | Edge weight |

**Example Request**

```json
{
  "edges": [
    {"vertices": [0, 1], "weight": 1},
    {"vertices": [1, 2], "weight": 1},
    {"vertices": [0, 2], "weight": 1}
  ],
  "options": {
    "num_restarts": 8,
    "random_seed": 7
  }
}
```

**Example Request (curl)**

```bash
curl -X POST http://localhost:8000/api/v2/solvers/qubo -H 'Content-Type: application/json' -d '{"edges":[{"vertices":[0,1],"weight":1},{"vertices":[1,2],"weight":1},{"vertices":[0,2],"weight":1}]}'
```

**Response `200`**

| Field | Type | Description |
|-------|------|-------------|
| `edges` | `DirectedEdge[]` | List of directed edges forming the optimized orientation |
| `optimized_graph_score` | `float` | Sum of all-pairs shortest path (APSP) distances in the directed graph |
| `bidirectional_graph_score` | `float` | Sum of APSP distances in the original undirected graph (baseline) |

**DirectedEdge**

| Field | Type | Description |
|-------|------|-------------|
| `_from` | `int` | Source vertex |
| `to` | `int` | Destination vertex |

**Example Response**

```json
{
  "edges": [
    {"_from": 0, "to": 1},
    {"_from": 1, "to": 2},
    {"_from": 2, "to": 0}
  ],
  "optimized_graph_score": 9.0,
  "bidirectional_graph_score": 6.0
}
```

**Errors**

| Status | Condition |
|--------|-----------|
| `400 Bad Request` | Invalid input (malformed edges, missing fields), an option the solver does not accept, or `robin` on a graph with a bridge |
| `404 Not Found` | Unknown `solver_name`; the message lists valid names |
| `408 Request Timeout` | Optimization exceeded the 10-second time limit |
| `422 Unprocessable Entity` | The solver cannot handle this graph — `qubo` on a graph too dense to split into QUBO-embeddable subgraphs. The message names the other solvers; `raw-sa` orients these |
| `500 Internal Server Error` | Solver ran but failed |
| `503 Service Unavailable` | Solver could not be constructed — e.g. missing D-Wave credentials |

---

## Solvers

| Name | Aliases | Method | Options | Needs D-Wave |
|------|---------|--------|---------|--------------|
| `raw-sa` | `sa` | Simulated annealing directly on graph metrics (APSP + flow), no QUBO | SA options | No |
| `qubo` | `dnc-qubo`, `dnc-qubo-sa` | Divide-and-conquer partitioning, subgraphs solved as QUBO with a local SA sampler. Dense graphs can fail to partition and return `422` | — | No |
| `robin` | `robbin` | Robbins orientation — single DFS pass that orients every edge | — | No |

### Options

**SA options** — accepted by `raw-sa` only

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `sweeps_per_temperature` | `int` | `2` | Sweeps performed at each temperature step |
| `num_restarts` | `int` | `4` | Independent annealing restarts; best result wins |
| `random_seed` | `int \| null` | `null` | Fixes the RNG for reproducible runs |
| `apsp_weight` | `float` | `1.0` | Weight of the APSP term in the cost function |
| `flow_weight` | `float` | `1.0` | Weight of the flow-conservation term |
| `disconnected_pair_penalty` | `float` | `10.0` | Penalty per unreachable vertex pair |

`qubo` and `robin` take no options and reject any `options` key with `400`. `GET /api/v2/solvers` is the authoritative list.

### `raw-sa` (alias `sa`)

- `mr2s-module`'s `SAMR2SSolver` — no QUBO; graph metrics are evaluated directly
- Randomly initializes edge directions, then flips single edges under the Metropolis criterion
- Cost combines a weighted APSP term (`apsp_weight`), a flow-conservation term (`flow_weight`), and a penalty per unreachable vertex pair (`disconnected_pair_penalty`)
- Runs `num_restarts` independent restarts and keeps the best
- Edge weights are used in both the APSP and flow terms
- Probabilistic — results vary between runs unless `random_seed` is fixed

### `qubo` (aliases `dnc-qubo`, `dnc-qubo-sa`)

- `mr2s-module`'s `DnCMr2sSolver` built on a QUBO inner solver (`create_dnc_qubo_sa_solver`)
- Partitions the graph by degeneracy pruning, solves each subgraph as a QUBO, then merges the orientations
- Inner QUBO variable encoding: `e_i_j = 0` → direction `i → j`, `e_i_j = 1` → direction `j → i`
- Samples via D-Wave's local `SimulatedAnnealingSampler`, so no credentials are needed
- Probabilistic — results may vary between runs
- If no valid partition exists, the request fails with `500` and a `DnC partition failed: ...` detail

### `robin` (alias `robbin`)

- `mr2s-module`'s `Robbin` — an `EdgeOrientationProtocol`, not an MR2S solver; the backend wraps it so it can be called like one
- Single DFS pass following Robbins' theorem: every edge is oriented at once, no search and no sampling
- Deterministic and by far the fastest option; useful as a baseline
- A bridge in the graph makes a strongly connected orientation impossible — the request then fails with `400`:

```json
{
  "detail": "Invalid input: no orientation found: the graph has a bridge, so no strongly connected orientation exists"
}
```

### Comparison

| | `raw-sa` | `qubo` | `robin` |
|---|---|---|---|
| **Method** | SA on graph metrics | DnC partition + QUBO/SA | Robbins DFS orientation |
| **Edge weights** | Used | Used | Ignored |
| **Deterministic** | No (unless `random_seed` set) | No | Yes |
| **Tunable** | 6 SA options | — | — |
| **Speed** | Moderate | Slowest | Fastest |
| **Fails when** | — | No valid partition | Graph has a bridge |

---

## Timeout

Optimization runs in a subprocess with a **10-second deadline**. On timeout, HTTP `408 Request Timeout` is returned.

---

## Scoring

| Score | Description |
|-------|-------------|
| `optimized_graph_score` | APSP sum of the **directed** solution graph |
| `bidirectional_graph_score` | APSP sum of the equivalent **undirected** graph (baseline for comparison) |

Lower scores indicate shorter average paths between vertices. A directed graph can never beat its undirected counterpart — the bidirectional score serves as the theoretical lower bound.

If the directed graph is not strongly connected, `optimized_graph_score` returns `-1`.

---

## v1 Endpoints

Unchanged and still supported. Each runs one fixed solver and ignores any `options` field.

| Endpoint | Solver | v2 equivalent |
|----------|--------|---------------|
| `POST /api/v1/mr2s` | `create_qubo_solver` — QUBO + local SA, no partitioning | Closest: `POST /api/v2/solvers/qubo` (adds DnC partitioning) |
| `POST /api/v1/raw-sa` | `create_sa_solver` | `POST /api/v2/solvers/raw-sa` |
| `POST /api/v1/brute-force` | Backend-local exhaustive 2^E search | Not exposed in v2 |

**Brute force** enumerates all 2^E orientations, computing APSP for each — O(2^E × V × (V + E)), practical up to ~20 edges. It is the only path that guarantees the global optimum, which is why it is kept for validating the other solvers on small graphs.

Request and response bodies are identical across v1 and v2, so migrating is a URL edit plus an optional `options` object.

---

## CORS

Allowed origins:
- `https://quantum-guardians.github.io`
- `https://mr2s.vercel.app`
- `https://qi4uinpnu.vercel.app`

Allowed methods: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`
Allowed headers: `Content-Type`, `Authorization`

---

## Data Types

### EdgeRequest

| Field | Type | Description |
|-------|------|-------------|
| `vertices` | `[integer, integer]` | Two vertex IDs of the undirected edge; order is ignored |
| `weight` | `integer` | Weight of the edge |

### DirectedEdge

| Field | Type | Description |
|-------|------|-------------|
| `_from` | `integer` | Source vertex ID |
| `to` | `integer` | Destination vertex ID |

### OptimizationResponse

| Field | Type | Description |
|-------|------|-------------|
| `edges` | `DirectedEdge[]` | Optimized directed edges |
| `optimized_graph_score` | `number` | Total APSP distance of the directed solution |
| `bidirectional_graph_score` | `number` | Total APSP distance of the undirected baseline |

### SolverInfo

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Canonical solver name |
| `description` | `string` | Human-readable summary |
| `options` | `string[]` | Accepted option keys |
| `requires_dwave_credentials` | `boolean` | Whether D-Wave credentials are required |
| `aliases` | `string[]` | Alternative names accepted on the path |
