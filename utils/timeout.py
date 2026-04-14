import asyncio
import functools
import multiprocessing

from fastapi import HTTPException

TIME_OUT = 10


def _worker(fn, args, kwargs, result_queue):
  """Runs fn(*args, **kwargs) in a child process and puts the result in result_queue."""
  try:
    result = fn(*args, **kwargs)
    result_queue.put(("ok", result))
  except Exception as e:
    result_queue.put(("error", e))


def _run_in_process(fn, args, kwargs):
  """
  Spawns a child process to execute fn(*args, **kwargs).
  Kills the process if it exceeds TIME_OUT seconds.
  Raises TimeoutError on timeout, or re-raises any exception from the child.
  """
  ctx = multiprocessing.get_context("fork")
  result_queue = ctx.Queue()
  process = ctx.Process(target=_worker, args=(fn, args, kwargs, result_queue))
  process.start()
  process.join(timeout=TIME_OUT)

  if process.is_alive():
    process.terminate()
    process.join(timeout=5)
    if process.is_alive():
      process.kill()
      process.join()
    raise TimeoutError()

  if not result_queue.empty():
    status, value = result_queue.get_nowait()
    if status == "ok":
      return value
    raise value

  raise RuntimeError(
    f"Worker process exited unexpectedly with code {process.exitcode}"
  )


def with_timeout(fn):
  @functools.wraps(fn)
  async def wrapper(*args, **kwargs):
    loop = asyncio.get_running_loop()
    try:
      return await loop.run_in_executor(
        None,
        functools.partial(_run_in_process, fn, args, kwargs),
      )
    except TimeoutError:
      raise HTTPException(
        status_code=408,
        detail=f"Optimization timed out after {TIME_OUT} seconds",
      )
  return wrapper
