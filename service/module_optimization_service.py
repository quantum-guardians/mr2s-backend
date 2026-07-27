from mr2s_module import (
  create_qubo_solver,
  create_sa_solver
)

from service.optimization_service import ProxyModuleOptimizationService

NONE_FACE_CYCLE_OPTIMIZATION_SERVICE = ProxyModuleOptimizationService(
  create_qubo_solver()
)

RAW_SA_OPTIMIZATION_SERVICE = ProxyModuleOptimizationService(
  create_sa_solver()
)