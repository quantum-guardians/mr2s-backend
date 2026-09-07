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


def _dnc_qubo_service(**_: Any) -> WeightedOptimizationService:
  from mr2s_module import create_dnc_qubo_sa_solver

  from service.optimization_service import ContractionFallbackService

  return ContractionFallbackService(
    contracted=create_dnc_qubo_sa_solver(use_reduction=True),
    plain=create_dnc_qubo_sa_solver(use_reduction=False),
  )


def _robbin_service(**_: Any) -> WeightedOptimizationService:
  from mr2s_module import create_robbin_solver

  from service.edge_orientation_service import RobbinOptimizationService

  return RobbinOptimizationService(create_robbin_solver())


SOLVER_SPECS: dict[str, SolverSpec] = {
  spec.name: spec
  for spec in (
    SolverSpec(
      name="raw-sa",
      description=(
        "Simulated annealing over graph metrics (APSP + flow), no QUBO. "
        "Degree-2 chains are contracted before solving."
      ),
      build_service=_module_solver_service("create_sa_solver"),
      option_names=_SIMULATED_ANNEALING_OPTIONS,
    ),
    SolverSpec(
      name="qubo",
      description=(
        "Divide-and-conquer partitioning, subgraphs solved as QUBO with "
        "a local simulated annealing sampler. Degree-2 chains are contracted "
        "when the contracted graph still partitions."
      ),
      build_service=_dnc_qubo_service,
    ),
    SolverSpec(
      name="robin",
      description=(
        "Robbins orientation: a DFS pass that orients every edge at once. "
        "Degree-2 chains are contracted before solving. Deterministic and "
        "fast, but fails when the graph has a bridge."
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
