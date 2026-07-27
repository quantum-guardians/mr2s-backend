from fastapi import APIRouter, HTTPException

from dto import ResponseDto, SolverInfoDto, SolverRequestDto
from service.solver_catalog import (
  SOLVER_ALIASES,
  SOLVER_SPECS,
  InvalidSolverOptionError,
  SolverUnavailableError,
  UnknownSolverError,
  create_optimization_service,
)
from utils import run_with_timeout

router = APIRouter(prefix="/api/v2/solvers", tags=["solvers"])


def _run_optimization(service, graph):
  tuples = service.optimize(graph)
  return ResponseDto.from_tuples(list(graph.get_vertices()), tuples)


def _aliases_of(solver_name: str) -> list[str]:
  return sorted(
    alias for alias, target in SOLVER_ALIASES.items() if target == solver_name
  )


@router.get("", response_model=list[SolverInfoDto])
async def list_solvers():
  return [
    SolverInfoDto(
      name=spec.name,
      description=spec.description,
      options=sorted(spec.option_names),
      requires_dwave_credentials=spec.requires_dwave_credentials,
      aliases=_aliases_of(spec.name),
    )
    for spec in SOLVER_SPECS.values()
  ]


@router.post("/{solver_name}", response_model=ResponseDto)
async def optimize_by_solver(solver_name: str, request: SolverRequestDto):
  try:
    service = create_optimization_service(solver_name, request.options)
  except UnknownSolverError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except InvalidSolverOptionError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except SolverUnavailableError as e:
    raise HTTPException(status_code=503, detail=str(e))

  try:
    graph = request.to_domain()
    return await run_with_timeout(_run_optimization, service, graph)
  except HTTPException:
    raise
  except ValueError as e:
    raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")
