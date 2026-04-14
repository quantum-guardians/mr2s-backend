from fastapi import APIRouter, HTTPException

from dto import WeightedRequestDto, ResponseDto
from service import (
  FlowConservationPolynomialGenerator,
  MinimizeSumOfApspPolynomialGenerator,
  SmallWorldSpec,
  NHop,
  PolynomialOptimizationService,
  NaotoService,
  BruteForceService,
)

router = APIRouter()

small_world_service = PolynomialOptimizationService(
  [
    FlowConservationPolynomialGenerator(),
    MinimizeSumOfApspPolynomialGenerator(
      SmallWorldSpec(
        n_hops=[
          NHop(n=2, weight=1),
          NHop(n=3, weight=1)
        ]
      )
    )
  ]
)

naoto_service = NaotoService()

brute_force_service = BruteForceService()

@router.post("/api/v1/mr2s", response_model=ResponseDto)
async def optimize_by_small_world(request: WeightedRequestDto):
  """
  API endpoint to optimize graph edge directions.

  This endpoint orchestrates the optimization and the scoring calculation.
  1. Calls the optimization service to get the directed graph.
  2. Calls the graph analyzer to calculate the APSP score for the new graph.
  3. Calls the graph analyzer to calculate the APSP score for the original
     bidirectional graph for comparison.
  4. Returns the final response including the graph and scores.
  """
  try:
    graph = request.to_domain()
    tuples = small_world_service.optimize(graph)
    return ResponseDto.from_tuples(list(graph.get_vertices()), tuples)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")

@router.post("/api/v1/raw-sa", response_model=ResponseDto)
async def optimize_by_naoto(request: WeightedRequestDto):
  try:
    graph = request.to_domain()
    tuples = naoto_service.optimize(graph)
    return ResponseDto.from_tuples(list(graph.get_vertices()), tuples)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")

@router.post("/api/v1/brute-force", response_model=ResponseDto)
async def optimize_brute_force(request: WeightedRequestDto):
  try:
    graph = request.to_domain()
    tuples = brute_force_service.optimize(graph)
    return ResponseDto.from_tuples(list(graph.get_vertices()), tuples)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")
