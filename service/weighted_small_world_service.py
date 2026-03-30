from dimod import BinaryPolynomial, Vartype, SampleSet

from domain import WeightedGraph, AdjEntry, WeightedEdge
from .qubo_utils import solve_binary_polynomial, multiply_polys
from .graph_analyzer import calculate_total_apsp_distance
from .optimization_service import WeightedOptimizationService


class WeightedSmallWorldService(WeightedOptimizationService):

  def _get_indicator_function(self, i: int, j: int, weight: int) -> BinaryPolynomial:
    if i == j:
      raise ValueError(f"i and j must be different, but both are {i}")

    if i < j:
      return BinaryPolynomial({(): weight, (f'e_{i}_{j}', ): -weight}, Vartype.BINARY)
    else:
      return BinaryPolynomial({(f'e_{j}_{i}',): weight}, Vartype.BINARY)


  def _get_2_hop_polynomial(
      self, vertices: set[int], adj: dict[int, list[AdjEntry]]
  ) -> BinaryPolynomial:
    term2_polynomial = BinaryPolynomial({}, Vartype.BINARY)
    for i in vertices:
      for k_entry in adj.get(i, []):
        for j_entry in adj.get(k_entry.vertex, []):
          if i == j_entry.vertex:
            continue
          # 모든 i -> k -> j
          temp: BinaryPolynomial = multiply_polys(
            self._get_indicator_function(i, k_entry.vertex, k_entry.weight),
            self._get_indicator_function(k_entry.vertex, j_entry.vertex, j_entry.weight)
          )
          temp.scale(-1)

          term2_polynomial.update(temp)

    return term2_polynomial

  def _get_3_hop_polynomial(
      self, vertices: set[int], adj: dict[int, list[AdjEntry]]
  ) -> BinaryPolynomial:
    term3_polynomial = BinaryPolynomial({}, Vartype.BINARY)
    for i in vertices:
      for j_entry in adj.get(i, []):
        for k_entry in adj.get(j_entry.vertex, []):
          for l_entry in adj.get(k_entry.vertex, []):
            if i == k_entry.vertex or j_entry.vertex == l_entry.vertex or i == l_entry.vertex:
              continue
            # 모든 i -> j -> k -> l
            temp = multiply_polys(
              self._get_indicator_function(i, j_entry.vertex, j_entry.weight),
              multiply_polys(
                self._get_indicator_function(j_entry.vertex, k_entry.vertex, k_entry.weight),
                self._get_indicator_function(k_entry.vertex, l_entry.vertex, l_entry.weight)
              )
            )
            temp.scale(-1)
            term3_polynomial.update(temp)
    return term3_polynomial


  def _build_polynomial(
      self, vertices: set[int], adj: dict[int, list[AdjEntry]], use_3hop_term: bool = True
  ) -> BinaryPolynomial:
    temp = self._get_2_hop_polynomial(vertices, adj)
    if use_3hop_term:
      temp.update(self._get_3_hop_polynomial(vertices, adj))
    return temp

  def _process_solution(
      self, best_sample: dict[str, int], canonical_edges: list[WeightedEdge]
  ) -> list[tuple[int, int]]:
    """
    Processes the best sample from the solver into a list of directed edge tuples.

    Returns:
        list[tuple[int, int]]: Directed edges represented as (u, v) integer node ID pairs.
    """
    final_edges = []
    for edge in canonical_edges:
      var_name = edge.to_key()
      if best_sample.get(var_name, 0) == 1:
        final_edges.append((edge.vertices[1], edge.vertices[0]))
      else:
        final_edges.append((edge.vertices[0], edge.vertices[1]))
    return final_edges

  def _select_best_sample(
      self,
      sample_set: SampleSet,
      canonical_edges: list[WeightedEdge],
      vertices: set[int]
  ) -> list[tuple[int, int]]:

    def get_effective_score(tuples: list[tuple[int, int]]):
      score = calculate_total_apsp_distance(vertices, tuples, True)
      return float('inf') if score == -1 else score

    return min(
      map(lambda sample: self._process_solution(sample, canonical_edges), sample_set.samples()),
      key=get_effective_score
    )


  # --- Public Service Function ---
  def optimize(
      self,
      graph: WeightedGraph
  ) -> list[tuple[int, int]]:
    """
    Orchestrates the graph direction optimization process using the 'small-world' model.
    """
    if graph.is_empty():
      return []

    vertices = graph.get_vertices()
    adj = graph.get_adjacency_dict()
    canonical_edges = graph.edges
    binary_polynomial = self._build_polynomial(vertices, adj, True)

    sample_set = solve_binary_polynomial(binary_polynomial)
    return self._select_best_sample(sample_set, canonical_edges, vertices)