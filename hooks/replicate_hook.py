"""
PyInstaller Runtime Hook for Replicate
This hook patches importlib.metadata to handle missing package metadata
in bundled executables, particularly for the replicate package.
"""

import sys
from importlib import metadata

# Save original functions
_original_version = metadata.version
_original_distribution = metadata.distribution

def patched_version(distribution_name):
    """
    Patched version function that handles PackageNotFoundError gracefully
    """
    try:
        return _original_version(distribution_name)
    except metadata.PackageNotFoundError:
        # Return sensible defaults for common packages when metadata not found
        package_defaults = {
            'replicate': '0.0.1',
            'requests': '2.31.0',
            'python-dotenv': '1.0.0',
            'ultralytics': '8.0.0',
            'torch': '2.0.0',
            'opencv-python': '4.8.0',
            'numpy': '1.24.0',
            'pillow': '10.0.0',
        }

        pkg_lower = distribution_name.lower().replace('_', '-')
        if pkg_lower in package_defaults:
            return package_defaults[pkg_lower]

        raise

def patched_distribution(distribution_name):
    """
    Patched distribution function that handles PackageNotFoundError gracefully
    """
    try:
        return _original_distribution(distribution_name)
    except metadata.PackageNotFoundError:
        # For replicate and other known packages, provide minimal distribution info
        if distribution_name.lower() in ['replicate', 'requests', 'python-dotenv']:
            # Create a minimal distribution object
            class MinimalDistribution:
                def __init__(self, name, version):
                    self.name = name
                    self.version = version

                def read_text(self, filename):
                    return None

            pkg_lower = distribution_name.lower().replace('_', '-')
            defaults = {
                'replicate': '0.0.1',
                'requests': '2.31.0',
                'python-dotenv': '1.0.0',
            }
            if pkg_lower in defaults:
                return MinimalDistribution(distribution_name, defaults[pkg_lower])

        raise

# Monkey-patch the metadata module functions
metadata.version = patched_version
metadata.distribution = patched_distribution

# Also patch importlib_metadata if it's being used (older packages)
try:
    import importlib_metadata
    importlib_metadata.version = patched_version
    importlib_metadata.distribution = patched_distribution
except ImportError:
    pass
