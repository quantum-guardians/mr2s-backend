from importlib import import_module
from typing import Any
from utils.timeout import run_with_timeout, TIME_OUT

__all__ = ["run_with_timeout", "TIME_OUT"]



_MODULE_ATTRS = {
    "run_with_timeout": (".timeout", "run_with_timeout"),
    "TIME_OUT": (".timeout", "TIME_OUT"),
}


def __getattr__(name: str) -> Any:
    """
    Lazily import attributes from submodules when accessed.

    This avoids eagerly importing heavy dependencies when `utils`
    is imported, while preserving the public API.
    """
    try:
        module_name, attr_name = _MODULE_ATTRS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(module_name, __name__)
    return getattr(module, attr_name)
