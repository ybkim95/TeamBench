"""
Custom exceptions for the library.
These exception types are part of the public API - do not rename or remove.
"""


class LibraryError(Exception):
    """Base exception for library errors."""
    pass


class ConfigError(LibraryError):
    """Raised when configuration is invalid."""
    pass


class ProcessingError(LibraryError):
    """Raised when processing fails unrecoverably."""
    pass
