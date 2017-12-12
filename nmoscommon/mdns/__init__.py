try:
    import avahi
except: # pragma: no cover
    from bonjour import MDNSEngine
else: # pragma: no cover
    from avahidbus import MDNSEngine

__all__ = [ "MDNSEngine" ]
