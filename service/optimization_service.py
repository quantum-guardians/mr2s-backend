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
    return list(solution.edges)
