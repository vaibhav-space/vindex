import sys
from typing import Any

if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points  # type: ignore[import-not-found]


def load_plugins(group: str) -> dict[str, Any]:
    """Dynamically load plugins registered under a specific entry point group."""
    loaded_plugins = {}
    try:
        eps = entry_points(group=group)
        for ep in eps:
            try:
                loaded_plugins[ep.name] = ep.load()
            except Exception:
                # Silently ignore plugins that fail to load to keep core robust
                pass
    except Exception:
        pass
    return loaded_plugins


def get_extractor_plugins() -> dict[str, Any]:
    """Retrieve all custom extractor plugins."""
    return load_plugins("vindex.extractors")


def get_runtime_plugins() -> dict[str, Any]:
    """Retrieve all custom runtime plugins."""
    return load_plugins("vindex.runtimes")


def get_output_plugins() -> dict[str, Any]:
    """Retrieve all custom output format plugins."""
    return load_plugins("vindex.outputs")
