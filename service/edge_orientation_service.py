from dataclasses import dataclass

from domain import WeightedGraph
from service import ModuleSolverProtocol
from service.optimization_service import ProxyModuleOptimizationService

BRIDGE_MESSAGE = (
  "no orientation found: the graph has a bridge, so no strongly "
  "connected orientation exists"
)


@dataclass
class RobbinOptimizationService(ProxyModuleOptimizationService):
  """Runs the Robbins solver and reports the bridge case in API terms.

  `Robbin` returns no oriented edges when the graph has a bridge, and the
  `RobbinMR2SSolver` wrapper around it turns that into a `ValueError` naming the
  first edge it could not orient. That is the only way this solver fails, so the
  message is rewritten into the bridge explanation the API has always returned.
  """

  mr2s_solver: ModuleSolverProtocol

  def optimize(self, graph: WeightedGraph) -> list[tuple[int, int]]:
    try:
      return super().optimize(graph)
    except ValueError as e:
      raise ValueError(BRIDGE_MESSAGE) from e
