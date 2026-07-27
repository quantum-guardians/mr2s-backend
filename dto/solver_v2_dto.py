from dataclasses import dataclass, field
from typing import Any

from domain import WeightedGraph
from dto.request_v1_dto import WeightedEdgeDto


@dataclass
class SolverRequestDto:
  edges: list[WeightedEdgeDto]
  options: dict[str, Any] = field(default_factory=dict)

  def to_domain(self) -> WeightedGraph:
    return WeightedGraph([edge.to_domain() for edge in self.edges])


@dataclass
class SolverInfoDto:
  name: str
  description: str
  options: list[str]
  requires_dwave_credentials: bool
  aliases: list[str]
