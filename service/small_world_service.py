from typing import Dict, Set, Tuple, List

from dimod import BinaryPolynomial, Vartype, SampleSet
from .graph_utils import to_canonical_edges, to_adjacency_dict
from .qubo_utils import solve_binary_polynomial, multiply_polys
from .graph_analyzer import calculate_total_apsp_distance
from .optimization_service import OptimizationService

class SmallWorldService(OptimizationService):

  def _get_indicator_function(self, i: int, j: int) -> BinaryPolynomial:
    if i == j:
      raise ValueError(f"i and j must be different, but both are {i}")

    if (i < j):
      return BinaryPolynomial({(): 1, (f'e_{i}_{j}', ): -1}, Vartype.BINARY)
    else:
      return BinaryPolynomial({(f'e_{j}_{i}',): 1}, Vartype.BINARY)


  def _get_2_hop_polynomial(
      self, vertices: Set[int], adj: Dict[int, List[int]]
  ) -> BinaryPolynomial:
    term2_polynomial = BinaryPolynomial({}, Vartype.BINARY)
    for i in vertices:
      for k in adj.get(i, []):
        for j in adj.get(k, []):
          if i == j:
            continue
          # 모든 i -> k -> j
          temp: BinaryPolynomial = multiply_polys(
            self._get_indicator_function(i, k),
            self._get_indicator_function(k, j)
          )
          temp.scale(-1)

          term2_polynomial.update(temp)

    return term2_polynomial

  def _get_3_hop_polynomial(
      self, vertices: Set[int], adj: Dict[int, List[int]]
  ) -> BinaryPolynomial:
    term3_polynomial = BinaryPolynomial({}, Vartype.BINARY)
    for i in vertices:
      for j in adj.get(i, []):
        for k in adj.get(j, []):
          for l in adj.get(k, []):
            if i == k or j == l or i == l:
              continue
            # 모든 i -> j -> k -> l
            temp = multiply_polys(
              self._get_indicator_function(i, j),
              multiply_polys(
                self._get_indicator_function(j, k),
                self._get_indicator_function(k, l)
              )
            )
            temp.scale(-1)
            term3_polynomial.update(temp)
    return term3_polynomial


  def _build_polynomial(
      self, vertices: Set[int], adj: Dict[int, List[int]], use_3hop_term: bool = True
  ) -> BinaryPolynomial:
    temp = self._get_2_hop_polynomial(vertices, adj)
    if use_3hop_term:
      temp.update(self._get_3_hop_polynomial(vertices, adj))
    return temp

  def _process_solution(
      self, best_sample: Dict[str, int], canonical_edges: Set[Tuple[int, int]]
  ) -> list[tuple[int, int]]:
      """
      Processes the best sample from the solver into a list of directed edge tuples.

      Returns:
          list[tuple[int, int]]: Directed edges represented as (u, v) integer node ID pairs.
      """
      final_edges = []
      for u_canon, v_canon in canonical_edges:
          var_name = f"e_{u_canon}_{v_canon}"
          if best_sample.get(var_name, 0) == 1:
              final_edges.append((v_canon, u_canon))
          else:
              final_edges.append((u_canon, v_canon))
      return final_edges

  def _select_best_sample(
      self,
      sample_set: SampleSet,
      canonical_edges: Set[Tuple[int, int]],
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
      vertices: set[int],
      edges: list[list[int]],
  ) -> list[tuple[int, int]]:
      """
      Orchestrates the graph direction optimization process using the 'small-world' model.
      """
      if not edges:
          return []

      canonical_edges = to_canonical_edges(edges)
      adj = to_adjacency_dict(canonical_edges)

      binary_polynomial = self._build_polynomial(vertices, adj, True)

      sample_set = solve_binary_polynomial(binary_polynomial)
      return self._select_best_sample(sample_set, canonical_edges, vertices)