from fastapi import APIRouter, HTTPException

from dto import WeightedRequestDto, ResponseDto
from service import (
  FlowConservationPolynomialGenerator,
  MinimizeSumOfApspPolynomialGenerator,
  SmallWorldSpec,
  NHop,
  PolynomialOptimizationService,
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
@router.post("/api/v1/optimize/small-world", response_model=ResponseDto)
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

@router.post("/api/v1/optimize/naoto", response_model=ResponseDto)
async def optimize_by_naoto(request: WeightedRequestDto):
  raise HTTPException(status_code=500, detail="Not implemented yet")