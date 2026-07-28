from importlib import import_module
from typing import Any

_MODULE_ATTRS = {
    "WeightedOptimizationService": (".optimization_service", "WeightedOptimizationService"),
    "ProxyModuleOptimizationService": (".optimization_service", "ProxyModuleOptimizationService"),
    "ModuleSolverProtocol": (".module_solver_protocol", "ModuleSolverProtocol"),
    "calculate_total_apsp_distance": (".graph_analyzer", "calculate_total_apsp_distance"),
    "BruteForceService": (".bruteforce_service", "BruteForceService"),
    "NONE_FACE_CYCLE_OPTIMIZATION_SERVICE": (".module_optimization_service", "NONE_FACE_CYCLE_OPTIMIZATION_SERVICE"),
    "RAW_SA_OPTIMIZATION_SERVICE": (".module_optimization_service", "RAW_SA_OPTIMIZATION_SERVICE"),
    "ProxyEdgeOrientationService": (".edge_orientation_service", "ProxyEdgeOrientationService"),
    "SOLVER_SPECS": (".solver_catalog", "SOLVER_SPECS"),
    "SOLVER_ALIASES": (".solver_catalog", "SOLVER_ALIASES"),
    "SolverSpec": (".solver_catalog", "SolverSpec"),
    "create_optimization_service": (".solver_catalog", "create_optimization_service"),
    "resolve_solver_spec": (".solver_catalog", "resolve_solver_spec"),
    "unsolvable_graph_detail": (".solver_catalog", "unsolvable_graph_detail"),
    "UnknownSolverError": (".solver_catalog", "UnknownSolverError"),
    "InvalidSolverOptionError": (".solver_catalog", "InvalidSolverOptionError"),
    "SolverUnavailableError": (".solver_catalog", "SolverUnavailableError"),
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
