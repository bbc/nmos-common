from __future__ import absolute_import
from __future__ import print_function

try:
    import avahi  # noqa: F401
except ImportError:  # pragma: no cover
    from .bonjour import MDNSEngine
else:  # pragma: no cover
    from .avahidbus import MDNSEngine

__all__ = ["MDNSEngine"]
