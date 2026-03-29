from abc import ABC, abstractmethod

class OptimizationService(ABC):

  @abstractmethod
  def optimize(
      self,
      vertices: set[int],
      edges: list[list[int]]
  ) -> list[tuple[int, int]]:
    pass