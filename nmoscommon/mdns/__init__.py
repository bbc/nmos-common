from __future__ import print_function
from __future__ import absolute_import

try:
    import avahi
except: # pragma: no cover
    from .bonjour import MDNSEngine
else: # pragma: no cover
    from .avahidbus import MDNSEngine

__all__ = ["MDNSEngine"]
