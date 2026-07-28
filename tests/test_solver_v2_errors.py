import asyncio
import importlib

import pytest
from fastapi import HTTPException

from dto import SolverRequestDto
from dto.request_v1_dto import WeightedEdgeDto
# The router package rebinds the name `solver_v2_router` to the APIRouter
# instance, so the module itself has to come from importlib.
solver_v2_module = importlib.import_module("router.solver_v2_router")
from service.solver_catalog import unsolvable_graph_detail

PARTITION_ERROR = RuntimeError(
  "DnC partition failed: input graph is not embeddable and no embeddable "
  "subgraph partition was found (vertices=12, edges=17)"
)


class FailingService:
  """Module-level so the 'spawn' start method can pickle it."""

  def __init__(self, error):
    self.error = error

  def optimize(self, graph):
    raise self.error


def triangle_request():
  return SolverRequestDto(
    edges=[
      WeightedEdgeDto(vertices=[1, 2], weight=1),
      WeightedEdgeDto(vertices=[2, 3], weight=1),
      WeightedEdgeDto(vertices=[1, 3], weight=1),
    ]
  )


def run_solver(monkeypatch, solver_name, error):
  monkeypatch.setattr(
    solver_v2_module,
    "create_optimization_service",
    lambda name, options: FailingService(error),
  )
  return asyncio.run(
    solver_v2_module.optimize_by_solver(solver_name, triangle_request())
  )


def test_partition_failure_is_reported_as_unprocessable(monkeypatch):
  with pytest.raises(HTTPException) as excinfo:
    run_solver(monkeypatch, "qubo", PARTITION_ERROR)

  assert excinfo.value.status_code == 422
  assert "raw-sa" in excinfo.value.detail


def test_other_runtime_errors_stay_server_errors(monkeypatch):
  with pytest.raises(HTTPException) as excinfo:
    run_solver(monkeypatch, "qubo", RuntimeError("Worker process exited unexpectedly"))

  assert excinfo.value.status_code == 500


def test_detail_resolves_aliases_and_excludes_the_failing_solver():
  detail = unsolvable_graph_detail("dnc-qubo", PARTITION_ERROR)

  assert detail is not None
  assert "'qubo' cannot orient this graph" in detail
  assert "'raw-sa'" in detail and "'robin'" in detail


def test_detail_is_none_for_unrelated_errors():
  assert unsolvable_graph_detail("qubo", ValueError("Invalid input: no edges")) is None
