from dataclasses import dataclass
from abc import ABC, abstractmethod

import mr2s_module

from domain import WeightedGraph


class WeightedOptimizationService(ABC):

  @abstractmethod
  def optimize(self, graph: WeightedGraph) -> list[tuple[int, int]]:
    pass

@dataclass
class ProxyModuleOptimizationService(WeightedOptimizationService):
  mr2s_solver: mr2s_module.QuboMR2SSolver

  def optimize(self, graph: WeightedGraph) -> list[tuple[int, int]]:
    solution = self.mr2s_solver.run(graph.to_mr2s_graph())
    return list(solution.edges)
