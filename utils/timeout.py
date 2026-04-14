import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException

TIME_OUT = 10

_executor = ThreadPoolExecutor()


def with_timeout(fn):
  @functools.wraps(fn)
  async def wrapper(*args, **kwargs):
    loop = asyncio.get_event_loop()
    try:
      return await asyncio.wait_for(
        loop.run_in_executor(_executor, functools.partial(fn, *args, **kwargs)),
        timeout=TIME_OUT,
      )
    except asyncio.TimeoutError:
      raise HTTPException(
        status_code=408,
        detail=f"Optimization timed out after {TIME_OUT} seconds",
      )
  return wrapper
