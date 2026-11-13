"""Domain-specific failures."""


class DomainError(Exception):
    """Base class for violations of research-domain invariants."""


class InvalidOrderObservationError(DomainError):
    """Raised when an order observation cannot represent a valid domain value."""
