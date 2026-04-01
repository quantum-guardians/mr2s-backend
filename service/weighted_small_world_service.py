from dimod import BinaryPolynomial, Vartype, SampleSet
from dataclasses import dataclass

from domain import WeightedGraph, AdjEntry, WeightedEdge
from .qubo_utils import solve_binary_polynomial, multiply_polys, add_polys
from .graph_analyzer import calculate_total_apsp_distance
from .optimization_service import WeightedOptimizationService

@dataclass
class NHop:
  n: int
  weight: int

@dataclass
class SmallWorldSpec:
  n_hops: list[NHop]

@dataclass
class WeightedSmallWorldService(WeightedOptimizationService):

  small_world_spec: SmallWorldSpec

  def _get_indicator_function(self, i: int, j: int, weight: int) -> BinaryPolynomial:
    if i == j:
      raise ValueError(f"i and j must be different, but both are {i}")

    if i < j:
      return BinaryPolynomial({(): weight, (f'e_{i}_{j}', ): -weight}, Vartype.BINARY)
    else:
      return BinaryPolynomial({(f'e_{j}_{i}',): weight}, Vartype.BINARY)

  def _get_n_hop_polynomial(
      self,
      n: int,
      last_vertex: int,
      adj: dict[int, list[AdjEntry]],
      used_vertices: set[int],
      current_polynomial: BinaryPolynomial
  ) -> BinaryPolynomial:
    if n == 0: return current_polynomial

    term_n = BinaryPolynomial({}, Vartype.BINARY)

    for entry in adj.get(last_vertex, []):
      if entry.vertex in used_vertices: continue

      used_vertices.add(entry.vertex)
      step_poly = self._get_indicator_function(last_vertex, entry.vertex, entry.weight)
      temp = self._get_n_hop_polynomial(n-1, entry.vertex, adj, used_vertices, step_poly)
      term_n = add_polys(term_n, temp)
      used_vertices.remove(entry.vertex)

    return multiply_polys(term_n, current_polynomial)

  def _get_total_n_hop_polynomial(
      self,
      n_hop: NHop,
      vertices: set[int],
      adj: dict[int, list[AdjEntry]]
  ) -> BinaryPolynomial:
    term_n = BinaryPolynomial({}, Vartype.BINARY)
    used_vertices = set()
    for vertex in vertices:
      initial_poly = BinaryPolynomial({(): 1.0}, Vartype.BINARY)
      used_vertices.add(vertex)
      temp = self._get_n_hop_polynomial(n_hop.n, vertex, adj, used_vertices, initial_poly)
      used_vertices.remove(vertex)
      term_n = add_polys(term_n, temp)
    term_n.scale(n_hop.weight)
    return term_n

  def _build_polynomial(
      self, vertices: set[int], adj: dict[int, list[AdjEntry]]
  ) -> BinaryPolynomial:
    terms = BinaryPolynomial({}, Vartype.BINARY)
    for n_hop in self.small_world_spec.n_hops:
      temp = self._get_total_n_hop_polynomial(n_hop, vertices, adj)
      terms = add_polys(terms, temp)
    terms.scale(-1)
    return terms

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
    binary_polynomial = self._build_polynomial(vertices, adj)

    sample_set = solve_binary_polynomial(binary_polynomial)
    return self._select_best_sample(sample_set, canonical_edges, vertices)