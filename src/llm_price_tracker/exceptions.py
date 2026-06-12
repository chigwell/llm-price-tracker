"""Package exceptions."""


class PricingError(Exception):
    """Base class for pricing errors."""


class PricingFetchError(PricingError):
    """Raised when a provider pricing page cannot be fetched."""


class PricingParseError(PricingError):
    """Raised when a provider pricing page cannot be parsed."""


class PricingValidationError(PricingError):
    """Raised when parsed pricing data fails validation."""
