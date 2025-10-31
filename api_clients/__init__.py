"""API client modules - Replicate API only (lazy loading)"""

# Lazy loading for replicate_client to avoid import-time metadata errors
def __getattr__(name):
    """Lazy load replicate_client module attributes on first access"""
    if name == 'ReplicateClient':
        from .replicate_client import ReplicateClient
        return ReplicateClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    """List available attributes"""
    return ['ReplicateClient']

__all__ = ['ReplicateClient']
