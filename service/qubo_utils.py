import dimod
from dimod import BinaryPolynomial
from dwave.samplers import SimulatedAnnealingSampler

sampler = SimulatedAnnealingSampler()

def solve_binary_polynomial(
    polynomial: BinaryPolynomial,
    num_reads: int = 100
) -> dict[str, int]:
  """
  Solves the given QUBO problem using a simulated annealer.
  """
  coeffs = [abs(v) for k, v in polynomial.items() if k != ()]
  max_coeff = max(coeffs) if coeffs else 1.0

  # 2. 보통 최대 계수의 1.5 ~ 2배 정도를 주면 안전합니다.
  # 이 값을 strength로 전달합니다.
  bqm = dimod.make_quadratic(polynomial, strength=max_coeff * 2.0, vartype=dimod.BINARY)

  sampleset = sampler.sample(bqm, num_reads=num_reads)
  return sampleset.first.sample

def multiply_polys(
    poly1: BinaryPolynomial,
    poly2: BinaryPolynomial
) -> BinaryPolynomial:
  new_data = {}
  for term1, coef1 in poly1.items():
    for term2, coef2 in poly2.items():
      # 두 항의 변수들을 합침 (튜플 결합 후 정렬하여 중복 제거)
      new_term = tuple(sorted(set(term1) | set(term2)))
      new_coef = coef1 * coef2

      if new_term in new_data:
        new_data[new_term] += new_coef
      else:
        new_data[new_term] = new_coef

  return dimod.BinaryPolynomial(new_data, dimod.BINARY)