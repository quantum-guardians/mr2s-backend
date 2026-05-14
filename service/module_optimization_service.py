from mr2s_module import (
  QuboMR2SSolver,
  SAMR2SSolver
)

from service.optimization_service import ProxyModuleOptimizationService

NONE_FACE_CYCLE_OPTIMIZATION_SERVICE = ProxyModuleOptimizationService(
  QuboMR2SSolver()
)

RAW_SA_OPTIMIZATION_SERVICE = ProxyModuleOptimizationService(
  SAMR2SSolver()
)