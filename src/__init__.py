from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 仅类型检查，不实际执行
    from .service.api import app
    from .config.api import PORT
else:
    # 注册表
    _LAZY_IMPORTS = {
        'app': ('.service.api', 'app'),
        'PORT': ('.config.api', 'PORT'),
    }

_import_cache = {}


# 不存在属性访问控制
def __getattr__(name):
    if name in _LAZY_IMPORTS:
        if name not in _import_cache:
            module_path, attr_name = _LAZY_IMPORTS[name]
            module = __import__(f'src{module_path}', fromlist=[attr_name])
            _import_cache[name] = getattr(module, attr_name)
        return _import_cache[name]

    raise AttributeError(f"module 'src' has no attribute '{name}'")


# 显式控制 import * 行为
__all__ = list(_LAZY_IMPORTS.keys())
