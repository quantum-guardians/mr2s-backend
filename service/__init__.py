from importlib import import_module
from typing import Any

_MODULE_ATTRS = {
    "WeightedOptimizationService": (".optimization_service", "WeightedOptimizationService"),
    "ProxyModuleOptimizationService": (".optimization_service", "ProxyModuleOptimizationService"),
    "NONE_FACE_CYCLE_OPTIMIZATION_SERVICE": (".module_optimization_service", "NONE_FACE_CYCLE_OPTIMIZATION_SERVICE"),
    "ModuleSolverProtocol": (".module_solver_protocol", "ModuleSolverProtocol"),
    "calculate_total_apsp_distance": (".graph_analyzer", "calculate_total_apsp_distance"),
    "BruteForceService": (".bruteforce_service", "BruteForceService"),
    "NaotoService": (".naoto_service", "NaotoService"),
    "optimize_edge_orientations": (".naoto_service", "optimize_edge_orientations"),
    "generate_connected_graph": (".naoto_service", "generate_connected_graph"),
    "compute_planar_faces": (".naoto_service", "compute_planar_faces"),
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
