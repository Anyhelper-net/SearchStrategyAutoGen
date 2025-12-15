from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .service.api import app
    from .service.ws_client import Client
else:
    _LAZY_IMPORTS = {
        'app': ('.service.api', 'app'),
        'Client': ('.service.ws_client', 'Client')
    }

_import_cache = {}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        if name not in _import_cache:
            module_path, attr_name = _LAZY_IMPORTS[name]
            module = __import__(f'src{module_path}', fromlist=[attr_name])
            _import_cache[name] = getattr(module, attr_name)
        return _import_cache[name]

    raise AttributeError(f"module 'src' has no attribute '{name}'")


__all__ = list(_LAZY_IMPORTS.keys())
