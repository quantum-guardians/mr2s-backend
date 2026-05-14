from typing import Protocol

from mr2s_module import Graph, Solution


class ModuleSolverProtocol(Protocol):
  def run(self, graph: Graph) -> Solution:
    ...