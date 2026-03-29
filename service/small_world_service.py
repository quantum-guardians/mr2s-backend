from typing import Dict, Set, Tuple, List

from dimod import BinaryPolynomial, Vartype
from dto.ResponseDto import EdgeDto
from service.graph_utils import to_canonical_edges, extract_vertices, to_adjacency_dict
from service.qubo_utils import solve_binary_polynomial, multiply_polys

def _get_indicator_function(i: int, j: int) -> BinaryPolynomial:
  if i == j:
    raise ValueError(f"i and j must be different, but both are {i}")

  if (i < j):
    return BinaryPolynomial({(): 1, (f'e_{i}_{j}', ): -1}, Vartype.BINARY)
  else:
    return BinaryPolynomial({(f'e_{j}_{i}',): 1}, Vartype.BINARY)


def _get_2_hop_polynomial(
    vertices: Set[int], adj: Dict[int, List[int]]
) -> BinaryPolynomial:
  term2_polynomial = BinaryPolynomial({}, Vartype.BINARY)
  for i in vertices:
    for k in adj.get(i, []):
      for j in adj.get(k, []):
        if i == j:
          continue
        # 모든 i -> k -> j
        temp: BinaryPolynomial = multiply_polys(
          _get_indicator_function(i, k),
          _get_indicator_function(k, j)
        )
        temp.scale(-1)

        term2_polynomial.update(temp)

  return term2_polynomial

def _get_3_hop_polynomial(
    vertices: Set[int], adj: Dict[int, List[int]]
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
            _get_indicator_function(i, j),
            multiply_polys(
              _get_indicator_function(j, k),
              _get_indicator_function(k, l)
            )
          )
          temp.scale(-1)
          term3_polynomial.update(temp)
  return term3_polynomial


def _build_polynomial(
    vertices: Set[int], adj: Dict[int, List[int]], use_3hop_term: bool = True
) -> BinaryPolynomial:
  temp = _get_2_hop_polynomial(vertices, adj)
  if use_3hop_term:
    temp.update(_get_3_hop_polynomial(vertices, adj))
  return temp

def _process_solution(
    best_sample: Dict[str, int], canonical_edges: Set[Tuple[int, int]]
) -> list[EdgeDto]:
    """
    Processes the best sample from the solver into a list of directed EdgeDto objects.
    """
    final_edges = []
    for u_canon, v_canon in canonical_edges:
        var_name = f"e_{u_canon}_{v_canon}"
        if best_sample.get(var_name, 0) == 1:
            final_edges.append(EdgeDto(_from=v_canon, to=u_canon))
        else:
            final_edges.append(EdgeDto(_from=u_canon, to=v_canon))
    return final_edges

# --- Public Service Function ---

def solve_direction_optimization_small_world(
    vertices: list[int],
    edges: list[list[int]],
    use_3hop: bool = True
) -> list[EdgeDto]:
    """
    Orchestrates the graph direction optimization process using the 'small-world' model.
    """
    if not edges:
        return []

    canonical_edges = to_canonical_edges(edges)
    vertex_set = extract_vertices(edges, vertices)
    adj = to_adjacency_dict(canonical_edges)

    binary_polynomial = _build_polynomial(vertex_set, adj, use_3hop)

    best_sample = solve_binary_polynomial(binary_polynomial)
    return _process_solution(best_sample, canonical_edges)