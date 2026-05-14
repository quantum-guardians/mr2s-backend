from mr2s_module import (
  QuboMR2SSolver,
  SAQuboSolver,
  SmallWorldSpec,
)

from service.optimization_service import ProxyModuleOptimizationService

NONE_FACE_CYCLE_OPTIMIZATION_SERVICE = ProxyModuleOptimizationService(
  QuboMR2SSolver()
)
