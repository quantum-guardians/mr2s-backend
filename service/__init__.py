from importlib import import_module
from typing import Any

__all__ = [
    "OptimizationService",
    "SmallWorldService",
    "optimize_edge_orientations",
    "generate_connected_graph",
    "compute_planar_faces",
    "calculate_total_apsp_distance",
    "extract_vertices",
    "to_canonical_edges",
    "to_adjacency_dict",
    "solve_binary_polynomial",
    "multiply_polys",
]

_MODULE_ATTRS = {
    "OptimizationService": (".optimization_service", "OptimizationService"),
    "SmallWorldService": (".small_world_service", "SmallWorldService"),
    "optimize_edge_orientations": (".naoto_service", "optimize_edge_orientations"),
    "generate_connected_graph": (".naoto_service", "generate_connected_graph"),
    "compute_planar_faces": (".naoto_service", "compute_planar_faces"),
    "calculate_total_apsp_distance": (".graph_analyzer", "calculate_total_apsp_distance"),
    "extract_vertices": (".graph_utils", "extract_vertices"),
    "to_canonical_edges": (".graph_utils", "to_canonical_edges"),
    "to_adjacency_dict": (".graph_utils", "to_adjacency_dict"),
    "solve_binary_polynomial": (".qubo_utils", "solve_binary_polynomial"),
    "multiply_polys": (".qubo_utils", "multiply_polys"),
}

def __getattr__(name: str) -> Any:
    """
    Lazily import attributes from submodules when accessed.

    This avoids eagerly importing heavy dependencies when `service`
    is imported, while preserving the public API.
    """
    try:
        module_name, attr_name = _MODULE_ATTRS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(module_name, __name__)
    return getattr(module, attr_name)
