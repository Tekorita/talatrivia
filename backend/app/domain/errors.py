"""Domain exceptions."""


class DomainError(Exception):
    """Base exception for domain errors."""
    pass


class NotFoundError(DomainError):
    """Raised when a resource is not found."""
    pass


class ForbiddenError(DomainError):
    """Raised when an operation is forbidden."""
    pass


class InvalidStateError(DomainError):
    """Raised when an operation is invalid for the current state."""
    pass


class ConflictError(DomainError):
    """Raised when there's a conflict (e.g., duplicate resource)."""
    pass

