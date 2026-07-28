from dataclasses import dataclass, field
from typing import Any, Callable

from service.optimization_service import (
  ProxyModuleOptimizationService,
  WeightedOptimizationService,
)


class UnknownSolverError(ValueError):
  """Raised when a requested solver name is not registered."""


class InvalidSolverOptionError(ValueError):
  """Raised when a request carries options the solver does not accept."""


class SolverUnavailableError(RuntimeError):
  """Raised when a registered solver cannot be constructed (e.g. missing credentials)."""


@dataclass(frozen=True)
class SolverSpec:
  name: str
  description: str
  build_service: Callable[..., WeightedOptimizationService]
  option_names: frozenset[str] = field(default_factory=frozenset)
  requires_dwave_credentials: bool = False


_SIMULATED_ANNEALING_OPTIONS = frozenset({
  "sweeps_per_temperature",
  "num_restarts",
  "random_seed",
  "apsp_weight",
  "flow_weight",
  "disconnected_pair_penalty",
})


def _module_solver_service(factory_name: str) -> Callable[..., WeightedOptimizationService]:
  """Builds a service that delegates to an mr2s_module solver.

  ``mr2s_module`` is imported lazily so that listing solvers never pays the
  import cost.
  """

  def build(**options: Any) -> WeightedOptimizationService:
    import mr2s_module

    create_solver = getattr(mr2s_module, factory_name)
    return ProxyModuleOptimizationService(create_solver(**options))

  return build


def _robbin_service(**_: Any) -> WeightedOptimizationService:
  from mr2s_module import Robbin

  from service.edge_orientation_service import ProxyEdgeOrientationService

  return ProxyEdgeOrientationService(Robbin())


SOLVER_SPECS: dict[str, SolverSpec] = {
  spec.name: spec
  for spec in (
    SolverSpec(
      name="raw-sa",
      description=(
        "Simulated annealing over graph metrics (APSP + flow), no QUBO."
      ),
      build_service=_module_solver_service("create_sa_solver"),
      option_names=_SIMULATED_ANNEALING_OPTIONS,
    ),
    SolverSpec(
      name="qubo",
      description=(
        "Divide-and-conquer partitioning, subgraphs solved as QUBO with "
        "a local simulated annealing sampler."
      ),
      build_service=_module_solver_service("create_dnc_qubo_sa_solver"),
    ),
    SolverSpec(
      name="robin",
      description=(
        "Robbins orientation: a DFS pass that orients every edge at once. "
        "Deterministic and fast, but returns no edges when the graph has a bridge."
      ),
      build_service=_robbin_service,
    ),
  )
}

SOLVER_ALIASES: dict[str, str] = {
  "sa": "raw-sa",
  "dnc-qubo": "qubo",
  "dnc-qubo-sa": "qubo",
  "robbin": "robin",
}


# The divide-and-conquer QUBO solver raises a plain RuntimeError when it cannot
# cut a graph into embeddable subgraphs, so the message prefix is the only
# marker available. A typed exception is tracked upstream in
# quantum-guardians/mr2s-module#78; switch to it once released.
PARTITION_FAILURE_PREFIX = "DnC partition failed"


def unsolvable_graph_detail(solver_name: str, error: Exception) -> str | None:
  """Describes `error` as a graph the solver cannot handle.

  Returns None when the error is a genuine server failure (the caller should
  keep reporting those as 5xx).
  """
  if not str(error).startswith(PARTITION_FAILURE_PREFIX):
    return None

  canonical_name = SOLVER_ALIASES.get(solver_name, solver_name)
  alternatives = ", ".join(
    f"'{name}'" for name in sorted(SOLVER_SPECS) if name != canonical_name
  )
  return (
    f"Solver '{canonical_name}' cannot orient this graph: it is too dense to "
    f"split into QUBO-embeddable subgraphs. Try another solver ({alternatives}) "
    f"or send a sparser graph. Underlying error: {error}"
  )


def resolve_solver_spec(name: str) -> SolverSpec:
  canonical_name = SOLVER_ALIASES.get(name, name)
  spec = SOLVER_SPECS.get(canonical_name)
  if spec is None:
    raise UnknownSolverError(
      f"Unknown solver '{name}'. Available: {', '.join(sorted(SOLVER_SPECS))}"
    )
  return spec


def create_optimization_service(
    name: str,
    options: dict[str, Any] | None = None,
) -> WeightedOptimizationService:
  spec = resolve_solver_spec(name)
  options = options or {}

  rejected = sorted(set(options) - spec.option_names)
  if rejected:
    accepted = ", ".join(sorted(spec.option_names)) or "none"
    raise InvalidSolverOptionError(
      f"Solver '{spec.name}' does not accept options: {', '.join(rejected)}. "
      f"Accepted options: {accepted}"
    )

  try:
    return spec.build_service(**options)
  except (InvalidSolverOptionError, UnknownSolverError):
    raise
  except TypeError as e:
    raise InvalidSolverOptionError(f"Invalid options for solver '{spec.name}': {e}") from e
  except Exception as e:
    raise SolverUnavailableError(f"Solver '{spec.name}' is unavailable: {e}") from e
