from dataclasses import dataclass
from typing import Protocol

from mr2s_module.domain import Edge, Graph

from domain import WeightedGraph
from service.optimization_service import WeightedOptimizationService


class EdgeOrientationProtocol(Protocol):
  def run(self, graph: Graph):
    ...


@dataclass
class ProxyEdgeOrientationService(WeightedOptimizationService):
  """Adapts an mr2s_module edge-orientation algorithm to the service interface.

  Orientation algorithms return `OrientedEdges` (directed `Edge` objects) rather
  than the `Solution` (edge tuples) produced by the MR2S solvers.
  """

  orientation: EdgeOrientationProtocol

  def optimize(self, graph: WeightedGraph) -> list[tuple[int, int]]:
    result = self.orientation.run(graph.to_mr2s_graph())
    edges = result.get_edges()
    if not edges and not graph.is_empty():
      raise ValueError(
        "no orientation found: the graph has a bridge, so no strongly "
        "connected orientation exists"
      )
    return [self._to_tuple(edge) for edge in edges]

  @staticmethod
  def _to_tuple(edge: Edge) -> tuple[int, int]:
    # `Edge.vertices` is (tail, head) once the edge is directed.
    tail, head = edge.vertices
    return tail, head
