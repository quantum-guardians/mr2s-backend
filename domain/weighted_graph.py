from collections import defaultdict
from dataclasses import dataclass
from typing import NamedTuple

import mr2s_module


@dataclass
class WeightedEdge:
  vertices: list[int] # Only use 0, 1 index for origin to destination
  weight: int

  def to_key(self) -> str:
    return f"e_{min(self.vertices)}_{max(self.vertices)}"

  def to_mr2s_edge(self) -> mr2s_module.Edge:
    return mr2s_module.Edge(
      vertex1=self.vertices[0],
      vertex2=self.vertices[1],
      weight=self.weight,
      directed=False,
    )

class AdjEntry(NamedTuple):
  vertex: int # Could be destination or origin vertex
  weight: int

@dataclass
class WeightedGraph:
  edges: list[WeightedEdge]

  def __post_init__(self):
    for edge in self.edges:
      edge.vertices.sort()

  def is_empty(self):
    return len(self.edges) == 0

  def get_vertices(self) -> set[int]:
    return {v for edge in self.edges for v in edge.vertices}

  def get_adjacency_dict(self) -> dict[int, list[AdjEntry]]:
    adj = defaultdict(list)
    for edge in self.edges:
      adj[edge.vertices[0]].append(AdjEntry(edge.vertices[1], edge.weight))
      adj[edge.vertices[1]].append(AdjEntry(edge.vertices[0], edge.weight))
    return dict(adj)

  def to_mr2s_graph(self) -> mr2s_module.Graph:
    return mr2s_module.Graph(
      [weighted_edge.to_mr2s_edge() for weighted_edge in self.edges]
    )
