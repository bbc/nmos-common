from __future__ import print_function
from __future__ import absolute_import

try:
    import zeroconf  # noqa: 401
except ImportError:
    try:
        import avahi  # noqa: 401
    except ImportError:  # pragma: no cover
        from .bonjour import MDNSEngine
    else:  # pragma: no cover
        from .avahidbus import MDNSEngine
else:
    from .zeroconfEngine.mdnsEngine import MDNSEngine

__all__ = ["MDNSEngine"]
