from fastapi import APIRouter, HTTPException

from dto import WeightedRequestDto, ResponseDto
from service import (
  BruteForceService,
)
from service.module_optimization_service import \
  NONE_FACE_CYCLE_OPTIMIZATION_SERVICE, RAW_SA_OPTIMIZATION_SERVICE
from utils import run_with_timeout


router = APIRouter()

brute_force_service = BruteForceService()

def _run_optimization(service, graph):
  tuples = service.optimize(graph)
  return ResponseDto.from_tuples(list(graph.get_vertices()), tuples)

@router.post("/api/v1/mr2s", response_model=ResponseDto)
async def optimize_by_small_world(request: WeightedRequestDto):
  try:
    graph = request.to_domain()
    return await run_with_timeout(
      _run_optimization,
      NONE_FACE_CYCLE_OPTIMIZATION_SERVICE,
      graph,
    )
  except HTTPException:
    raise
  except ValueError as e:
    raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")

@router.post("/api/v1/raw-sa", response_model=ResponseDto)
async def optimize_by_raw_sa(request: WeightedRequestDto):
  try:
    graph = request.to_domain()
    return await run_with_timeout(_run_optimization, RAW_SA_OPTIMIZATION_SERVICE, graph)
  except HTTPException:
    raise
  except ValueError as e:
    raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")

@router.post("/api/v1/brute-force", response_model=ResponseDto)
async def optimize_brute_force(request: WeightedRequestDto):
  try:
    graph = request.to_domain()
    return await run_with_timeout(_run_optimization, brute_force_service, graph)
  except HTTPException:
    raise
  except ValueError as e:
    raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")
