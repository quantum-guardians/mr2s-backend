from dataclasses import dataclass
from abc import ABC, abstractmethod

from domain import WeightedGraph
from service import ModuleSolverProtocol

class WeightedOptimizationService(ABC):
  @abstractmethod
  def optimize(self, graph: WeightedGraph) -> list[tuple[int, int]]:
    pass

@dataclass
class ProxyModuleOptimizationService(WeightedOptimizationService):
  mr2s_solver: ModuleSolverProtocol

  def optimize(self, graph: WeightedGraph) -> list[tuple[int, int]]:
    solution = self.mr2s_solver.run(graph.to_mr2s_graph())
    # `Solution.edges` maps edge id -> (tail, head); the ids are internal to
    # mr2s_module, so only the directions cross the API boundary.
    return list(solution.edges.values())


@dataclass
class ContractionFallbackService(WeightedOptimizationService):
  """Runs a solver with chain contraction, retrying without it if partitioning fails.

  Contraction raises the degeneracy of the QUBO interaction graph, so a graph
  that used to clear the DnC embedding prefilter can miss it and leave the
  partition search with nothing to return (mr2s-module#90). That verdict comes
  from an estimate made before any sampling, so the discarded attempt costs the
  partition search rather than a solve.

  Each attempt gets a fresh `Graph`: the solvers fix edge directions in place.
  """

  contracted: ModuleSolverProtocol
  plain: ModuleSolverProtocol

  def optimize(self, graph: WeightedGraph) -> list[tuple[int, int]]:
    try:
      solution = self.contracted.run(graph.to_mr2s_graph())
    except RuntimeError:
      solution = self.plain.run(graph.to_mr2s_graph())
    return list(solution.edges.values())
