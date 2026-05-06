from mr2s_module import (
  ApspSumRanker,
  Evaluator,
  FlowPolyGenerator,
  NHop,
  NHopPolyGenerator,
  QuboMR2SSolver,
  SAQuboSolver,
  SmallWorldSpec,
)

from service.optimization_service import ProxyModuleOptimizationService

def create_default_small_world_spec() -> SmallWorldSpec:
  return SmallWorldSpec(n_hops=[NHop(n=2, weight=1), NHop(n=3, weight=1)])

def create_n_hop_poly_generator(
  small_world_spec: SmallWorldSpec | None = None,
) -> NHopPolyGenerator:
  n_hop_poly_generator = NHopPolyGenerator()
  n_hop_poly_generator.small_world_spec = (
    small_world_spec if small_world_spec is not None else create_default_small_world_spec()
  )
  return n_hop_poly_generator

def create_none_face_cycle_qubo_mr2s_solver() -> QuboMR2SSolver:
  return QuboMR2SSolver(
    face_cycle=None,
    qubo_solver=SAQuboSolver(ranker=ApspSumRanker()),
    evaluator=Evaluator(),
    poly_generators={create_n_hop_poly_generator(), FlowPolyGenerator()},
  )

NONE_FACE_CYCLE_OPTIMIZATION_SERVICE = ProxyModuleOptimizationService(
  create_none_face_cycle_qubo_mr2s_solver()
)
